# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Uploads handler."""

import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

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

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        body = json.loads(event["body"])
        job_name: str = body["job_name"]
        works: list[dict[str, str]] = body["works"]
        table = dynamodb.Table(WORKS_TABLE_NAME)
        for work in works:
            work_id: str = work["work_id"]
            s3_uris: str = work["s3_uris"]
            # Add work item to SQS queue
            sqs_message = {"job_name": job_name, "work_id": work_id, "s3_uris": s3_uris}
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_message))
            logger.debug(f"Successfully added job={job_name} work={work_id} to SQS")
            # Put pending work item in DynamoDB
            ddb_work_item = {
                "job_name": job_name,
                "work_id": work_id,
                "s3_uris": s3_uris,
                "work_status": "IN_QUEUE",
            }
            table.put_item(Item=ddb_work_item)
            logger.debug(f"Successfully added job={job_name} work={work_id} to DynamoDB")
        logger.info(f"Successfully added all works for job={job_name} to SQS and DynamoDB")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Success"}),
            "headers": CORS_HEADERS,
        }
    except ClientError as e:
        logger.exception(f"Error generating presigned URL: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": CORS_HEADERS,
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": CORS_HEADERS,
        }
