# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Get job progress."""

import json
import logging
import os
from collections import defaultdict
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}
JOB_NAME = "job_name"
JOB_TYPE = "job_type"
WORK_ID = "work_id"
WORK_STATUS = "work_status"

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(WORKS_TABLE_NAME)

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


def query_all_items(job_name: str) -> list[dict]:
    """Query all items for a given job name, handling pagination."""
    items = []
    query_kwargs = {
        "KeyConditionExpression": Key(JOB_NAME).eq(job_name),
        "ProjectionExpression": f"{WORK_ID}, {WORK_STATUS}, {JOB_TYPE}",
    }

    while True:
        response = table.query(**query_kwargs)
        items.extend(response["Items"])

        if "LastEvaluatedKey" not in response:
            break

        query_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return items


def organize_items(items: list[dict]) -> tuple[dict[str, list[str]], str]:
    """Organize items by status and extract job type."""
    work_ids_by_status = defaultdict(list)
    job_types = set()

    for item in items:
        work_id = item.get(WORK_ID, None)
        job_type = item.get(JOB_TYPE, None)

        if work_id is None:
            msg = f"Field {WORK_ID} not found for item."
            logger.warning(msg)
            raise ValueError(msg)

        elif job_type is None:
            msg = f"Field {JOB_TYPE} not found for {WORK_ID}={work_id}."
            logger.warning(msg)
            raise ValueError(msg)

        else:
            work_ids_by_status[item[WORK_STATUS]].append(work_id)
            job_types.add(job_type)

    if len(job_types) > 1:
        msg = f"Multiple job types found for the same job: {job_types}."
        logger.warning(msg)
        raise ValueError(msg)

    return dict(work_ids_by_status), job_type


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler for getting job progress."""
    try:
        query_params = event.get("queryStringParameters", None)

        if not query_params:
            return create_response(400, {"error": f"Missing required query parameter: {JOB_NAME}"})

        job_name: str | None = query_params.get(JOB_NAME, None)

        if not job_name:
            return create_response(400, {"error": f"Missing required query parameter: {JOB_NAME}"})

        items = query_all_items(job_name)

        if len(items) == 0:
            return create_response(404, {"message": f"No data found for {JOB_NAME}={job_name}"})

        work_ids_by_status, job_type = organize_items(items)

        # Return success response
        response = {
            "job_progress": work_ids_by_status,
            "job_type": job_type,
        }
        return create_response(200, response)

    except ClientError as e:
        logger.exception(f"DynamoDB error: {e}")
        return create_response(500, {"error": "Database error", "details": str(e)})

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
