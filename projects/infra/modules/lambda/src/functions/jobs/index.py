# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Jobs handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict, List, Union

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(JOBS_TABLE_NAME)

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


def deserialize_dynamodb_item(raw_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Any:
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


def create_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def get_all_jobs() -> Dict[str, Any]:
    """Retrieve all jobs from DynamoDB."""
    try:
        response = table.scan()
        items = response.get("Items", [])
        deserialized_items = deserialize_dynamodb_item(items)

        logger.info(f"Retrieved {len(deserialized_items)} jobs")
        return create_response(200, {"jobs": deserialized_items})

    except ClientError as e:
        logger.error(f"DynamoDB error while scanning: {e}")
        raise


def get_specific_job(job_id: str) -> Dict[str, Any]:
    """Retrieve a specific job from DynamoDB."""
    try:
        response = table.get_item(Key={"job_id": job_id})
        item = response.get("Item")

        if not item:
            logger.warning(f"Job ID {job_id} not found")
            return create_response(404, {"error": "Job ID not found"})

        deserialized_item = deserialize_dynamodb_item(item)
        logger.info(f"Job {job_id} retrieved: {deserialized_item}")
        return create_response(200, deserialized_item)

    except ClientError as e:
        logger.error(f"DynamoDB error while retrieving job {job_id}: {e}")
        raise


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        query_params = event.get("queryStringParameters", {}) or {}
        job_id = query_params.get("job_id")

        return get_specific_job(job_id) if job_id else get_all_jobs()

    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {"error": "DynamoDB error"})

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
