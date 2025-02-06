# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Start ECS task handler."""

import json
import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
ECS_CLUSTER_NAME = os.environ["ECS_CLUSTER_NAME"]
ECS_TASK_DEFINITION_ARN = os.environ["ECS_TASK_DEFINITION_ARN"]
SUBNET_IDS = os.environ["ECS_SUBNET_IDS"].split(",")
SECURITY_GROUP_IDS = os.environ["ECS_SECURITY_GROUP_IDS"].split(",")

# Initialize AWS clients globally
ecs_client = boto3.client("ecs", region_name=AWS_REGION)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        logger.info("S3 Event received: %s", json.dumps(event))

        for record in event["Records"]:
            s3_event = record["s3"]
            bucket_name = s3_event["bucket"]["name"]
            object_key = s3_event["object"]["key"]
            logger.info(f"New object uploaded: {bucket_name}/{object_key}")

            try:
                # Start ECS task with the object key as an environment variable
                response = ecs_client.run_task(
                    cluster=ECS_CLUSTER_NAME,
                    taskDefinition=ECS_TASK_DEFINITION_ARN,
                    count=1,
                    launchType="FARGATE",
                    networkConfiguration={
                        "awsvpcConfiguration": {
                            "subnets": SUBNET_IDS,
                            "securityGroups": SECURITY_GROUP_IDS,
                            "assignPublicIp": "ENABLED",
                        }
                    },
                    overrides={
                        "containerOverrides": [
                            {
                                "name": "processing-container",
                                "environment": [{"name": "JOB_ID", "value": object_key}],
                            }
                        ]
                    },
                )
                logger.info(f"ECS task started: {response}")
            except ClientError as e:
                logger.exception(f"Failed to start ECS task for object {object_key}: {str(e)}")
                continue

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "ECS tasks started successfully"}),
        }
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
