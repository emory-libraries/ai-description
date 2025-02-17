# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Uploads handler."""

import json
import logging
import os
from typing import Any, Dict
from decimal import Decimal

import boto3

# Constants
AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}
JOB_NAME = "job_name"
JOB_TYPE = "job_type"
WORKS = "works"
WORK_ID = "work_id"
IMAGE_S3_URIS = "image_s3_uris"
CONTEXT_S3_URI = "context_s3_uri"
WORK_STATUS = "work_status"

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal type serialization."""

    def default(self, obj: Any) -> Any:
        """Default method."""
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        # Load args from event
        body = json.loads(event["body"])
        for required_key in (JOB_NAME, JOB_TYPE, WORKS):
            if required_key not in body:
                msg = f"{required_key} not present in request body"
                logger.exception(msg)
                create_response(400, msg)

        job_name: str = body[JOB_NAME]
        job_type: str = body[JOB_TYPE]
        works: list[dict[str, str]] = body[WORKS]
        table = dynamodb.Table(WORKS_TABLE_NAME)
        for work in works:
            work_id: str = work[WORK_ID]
            image_s3_uris: str = work[IMAGE_S3_URIS]
            context_s3_uri: str | None = work.get(CONTEXT_S3_URI, None)
            # Add work item to SQS queue
            sqs_message = {
                JOB_NAME: job_name,
                JOB_TYPE: job_type,
                WORK_ID: work_id,
                IMAGE_S3_URIS: image_s3_uris,
                CONTEXT_S3_URI: context_s3_uri,
            }
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_message))
            logger.debug(f"Successfully added job={job_name} work={work_id} to SQS")
            # Put pending work item in DynamoDB
            ddb_work_item = {
                JOB_NAME: job_name,
                JOB_TYPE: job_type,
                WORK_ID: work_id,
                IMAGE_S3_URIS: image_s3_uris,
                CONTEXT_S3_URI: context_s3_uri,
                WORK_STATUS: "IN_QUEUE",
            }
            table.put_item(Item=ddb_work_item)
            logger.debug(f"Successfully added job={job_name} work={work_id} to DynamoDB")
        logger.info(f"Successfully added all works for job={job_name} to SQS and DynamoDB")

        return create_response(200, json.dumps({"message": "Success"}))
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(500, json.dumps({"error": "Internal server error"}))
