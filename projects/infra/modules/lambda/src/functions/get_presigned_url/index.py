# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate Pre-signed S3 URL Lambda Function."""

import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
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
S3_URI = "s3_uri"
EXPIRES_IN = "expires_in"
DEFAULT_EXPIRATION = 3600  # Default expiration time (in seconds)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients globally
s3 = boto3.client("s3", config=S3_CONFIG, region_name=AWS_REGION)


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": CORS_HEADERS,
    }


def generate_presigned_url(s3_uri: str, expiration: int = DEFAULT_EXPIRATION) -> str:
    """Generate a presigned URL from an S3 URI.

    Args:
        s3_uri: The S3 URI in the format s3://bucket-name/path/to/object
        expiration: URL expiration time in seconds

    Returns:
        A presigned URL for the object
    """
    parsed_uri = urlparse(s3_uri)

    # Validate S3 URI format
    if parsed_uri.scheme != "s3":
        raise ValueError(f"Invalid S3 URI scheme: {parsed_uri.scheme}. Expected 's3'")

    bucket_name = parsed_uri.netloc
    object_key = parsed_uri.path.lstrip("/")

    if not bucket_name or not object_key:
        raise ValueError("S3 URI must contain both bucket name and object key")

    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": bucket_name, "Key": object_key}, ExpiresIn=expiration
        )
        return presigned_url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler to generate a presigned URL for an S3 object.

    Expected event format:
    - For direct Lambda invocation: {"s3_uri": "s3://bucket-name/path/to/object", "expires_in": 3600}
    - For API Gateway: query parameters with "s3_uri" and optional "expires_in"
    """
    try:
        # Extract parameters based on event source
        if "queryStringParameters" in event and event["queryStringParameters"]:
            # API Gateway invocation
            s3_uri = event["queryStringParameters"].get(S3_URI)
            expires_in_str = event["queryStringParameters"].get(EXPIRES_IN, str(DEFAULT_EXPIRATION))
        else:
            # Direct Lambda invocation
            s3_uri = event.get(S3_URI)
            expires_in_str = str(event.get(EXPIRES_IN, DEFAULT_EXPIRATION))

        # Validate required parameters
        if not s3_uri:
            logger.error("No S3 URI provided")
            return create_response(400, {"error": "Missing required parameter 's3_uri'"})

        # Parse expiration time
        try:
            expires_in = int(expires_in_str)
            if expires_in <= 0:
                expires_in = DEFAULT_EXPIRATION
        except (ValueError, TypeError):
            expires_in = DEFAULT_EXPIRATION

        # Generate the presigned URL
        presigned_url = generate_presigned_url(s3_uri, expires_in)

        # Return success response
        return create_response(
            200, {"presigned_url": presigned_url, "s3_uri": s3_uri, "expires_in_seconds": expires_in}
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return create_response(400, {"error": str(e)})
    except ClientError as e:
        logger.error(f"AWS service error: {str(e)}")
        return create_response(500, {"error": "Error accessing S3 resource"})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_response(500, {"error": "Internal server error"})
