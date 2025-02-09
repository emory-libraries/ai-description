# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Results handler."""

import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
S3_CONFIG = Config(
    {
        "s3": {"addressing_style": "virtual"},
        "signature_version": "s3v4",
    }
)
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
s3 = boto3.client("s3", region_name=AWS_REGION, config=S3_CONFIG)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(WORKS_TABLE_NAME)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        job_id = event["queryStringParameters"].get("job_id")

        if not job_id:
            logger.error("Missing job_id in query parameters")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing job_id parameter"}),
                "headers": CORS_HEADERS,
            }

        response = table.get_item(Key={"job_id": job_id})
        item = response.get("Item")

        if item and item["status"] == "COMPLETED":
            # Generate a presigned URL for the results
            logger.info(f"Generated presigned URL for job_id {job_id}")
            return {
                "statusCode": 200,
                "body": json.dumps({"job_id": job_id}),
                "headers": CORS_HEADERS,
            }
        else:
            logger.warning(f"Results not available for job_id {job_id}")
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Results not available"}),
                "headers": CORS_HEADERS,
            }
    except ClientError as e:
        logger.error(f"AWS service error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": CORS_HEADERS,
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": CORS_HEADERS,
        }
