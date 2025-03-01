# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Results handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.config import Config
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
S3_CONFIG = Config(
    s3={"addressing_style": "virtual"},
    signature_version="s3v4",
)
S3_KWARGS = {
    "config": S3_CONFIG,
    "region_name": AWS_REGION,
}
JOB_NAME = "job_name"
WORK_ID = "work_id"
IMAGE_S3_URIS = "image_s3_uris"
IMAGE_S3_PRESIGNED_URLS = "image_presigned_urls"

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
s3 = boto3.client("s3", config=S3_CONFIG, region_name=AWS_REGION)
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


def generate_presigned_urls(s3_uris: list[str]) -> list[str]:
    """Generate presigned URLS from S3 URIs."""
    s3 = boto3.client("s3", config=S3_CONFIG, region_name=AWS_REGION)
    presigned_urls = []

    for uri in s3_uris:
        parsed_uri = urlparse(uri)
        bucket_name = parsed_uri.netloc
        object_key = parsed_uri.path.lstrip("/")

        try:
            presigned_url = s3.generate_presigned_url(
                "get_object", Params={"Bucket": bucket_name, "Key": object_key}, ExpiresIn=60
            )
            presigned_urls.append(presigned_url)
        except Exception as e:
            print(f"Error generating presigned URL for {uri}: {str(e)}")
            presigned_urls.append(None)

    return presigned_urls


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

            image_s3_uris = deserialized_item[IMAGE_S3_URIS]
            deserialized_item[IMAGE_S3_PRESIGNED_URLS] = generate_presigned_urls(image_s3_uris)

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
