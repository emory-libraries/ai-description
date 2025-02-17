# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Jobs handler."""

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


def get_work_ids_by_job_name_and_status(job_name: str) -> dict[str, list[str]]:
    """Get work ids by job name and status"""
    try:
        response = table.query(
            KeyConditionExpression=Key(JOB_NAME).eq(job_name),
            ProjectionExpression=f"{WORK_ID}, {WORK_STATUS}",
        )

        items = response["Items"]

        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=Key(JOB_NAME).eq(job_name),
                ProjectionExpression=f"{WORK_ID}, {WORK_STATUS}",
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response["Items"])

        # Organize items by status
        organized_items = defaultdict(list)
        for item in items:
            organized_items[item[WORK_STATUS]].append(item[WORK_ID])

        # Convert defaultdict to regular dict
        return dict(organized_items)

    except Exception as e:
        logger.exception(f"Failed to get works for job {job_name}: {str(e)}")


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
        query_params = event.get("queryStringParameters", {})
        job_name: str = query_params.get(JOB_NAME)

        if not job_name:
            return create_response(400, {"error": f"Missing required query parameter: {JOB_NAME}"})

        work_ids_by_status: dict[str, list[str]] = get_work_ids_by_job_name_and_status(job_name)

        if not work_ids_by_status:
            return create_response(404, {"message": f"No data found for {JOB_NAME}={job_name}"})

        return create_response(200, work_ids_by_status)

    except ClientError as e:
        logger.exception(f"DynamoDB error: {e}")
        return create_response(500, {"error": "Database error", "details": str(e)})

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
