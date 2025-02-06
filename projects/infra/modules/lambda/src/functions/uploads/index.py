# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Uploads handler."""

import json
import logging
import os
import uuid
from typing import Any, Dict

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
UPLOADS_BUCKET_NAME = os.environ["UPLOADS_BUCKET_NAME"]
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
S3_CONFIG = Config(
    {
        "s3": {"addressing_style": "virtual"},
        "signature_version": "s3v4",
    }
)
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
s3 = boto3.client("s3", region_name=AWS_REGION, config=S3_CONFIG)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        job_id = str(uuid.uuid4())
        key = job_id

        # Generate a presigned URL for uploading
        response = s3.generate_presigned_post(
            Bucket=UPLOADS_BUCKET_NAME,
            Key=key,
            Conditions=[
                {"bucket": UPLOADS_BUCKET_NAME},
                {"key": key},
            ],
            ExpiresIn=3600,
        )
        logger.info(f"Generated presigned URL for job_id {job_id}")

        # Store initial job metadata
        table = dynamodb.Table(JOBS_TABLE_NAME)
        table.put_item(Item={"job_id": job_id, "status": "PENDING"})
        logger.info(f"Stored initial job metadata for job_id {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "content": response}),
            "headers": CORS_HEADERS,
        }
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {e}")
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
