# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Results handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.types import TypeDeserializer
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

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(WORKS_TABLE_NAME)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

deserializer = TypeDeserializer()


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal type serialization."""

    def default(self, obj: Any) -> Any:
        """Default method."""
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def deserialize_dynamodb_item(raw_data: dict[str, Any] | list[dict[str, Any]]) -> Any:
    """Deserialize DynamoDB data to native Python types."""
    if isinstance(raw_data, list):
        return [deserialize_dynamodb_item(item) for item in raw_data]

    if not isinstance(raw_data, dict):
        return raw_data

    deserialized_data = {}
    for key, value in raw_data.items():
        if isinstance(value, dict):
            try:
                deserialized_data[key] = deserializer.deserialize(value)
            except (TypeError, ValueError):
                deserialized_data[key] = deserialize_dynamodb_item(value)
        else:
            deserialized_data[key] = value

    return deserialized_data


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler."""
    try:
        job_name = event["queryStringParameters"].get(JOB_NAME)
        if not job_name:
            msg = f"Missing '{JOB_NAME}' in query parameters"
            logger.error(msg)
            return create_response(400, {"error": msg})

        work_id = event["queryStringParameters"].get(WORK_ID)
        if not work_id:
            msg = f"Missing '{WORK_ID}' in query parameters"
            logger.error(msg)
            return create_response(400, {"error": msg})

        response = table.get_item(Key={JOB_NAME: job_name, WORK_ID: work_id})
        item = response.get("Item")
        if item:
            deserialized_item = deserialize_dynamodb_item(item)
            return create_response(200, {"item": deserialized_item})

        else:
            logger.warning(f"Results not available for {JOB_NAME}={job_name} and {WORK_ID}={work_id}")
            return create_response(404, {"error": "Results not available"})

    except ClientError as e:
        logger.error(f"AWS service error: {e}")
        return create_response(500, {"error": "Internal server error"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
