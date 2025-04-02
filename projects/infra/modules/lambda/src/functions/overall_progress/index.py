# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Check status of queue and ECS."""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3

# Constants
AWS_REGION = os.environ["AWS_REGION"]
ECS_CLUSTER_NAME = os.environ["ECS_CLUSTER_NAME"]
ECS_TASK_DEFINITION_ARN = os.environ["ECS_TASK_DEFINITION_ARN"]
ECS_TASK_FAMILY_NAME = ECS_TASK_DEFINITION_ARN.split("/")[-1].split(":")[0]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
sqs = boto3.client("sqs", region_name=AWS_REGION)
ecs_client = boto3.client("ecs", region_name=AWS_REGION)

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


def get_ecs_status(cluster_name: str, task_family_name: str) -> str:
    """Checks if ECS task is running."""
    running_tasks = ecs_client.list_tasks(cluster=cluster_name, family=task_family_name, desiredStatus="RUNNING")
    if running_tasks["taskArns"]:
        return "Active"
    else:
        return "Inactive"


def get_queue_length(queue_url: str) -> int:
    """Get the approximate length of the queue.

    Args:
        queue_url (str): The URL of the SQS queue

    Returns:
        int: Approximate number of messages in the queue
    """
    # Create SQS client
    sqs = boto3.client("sqs")

    # Get queue attributes
    response = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["ApproximateNumberOfMessages"])

    # Extract the values
    queue_length = int(response["Attributes"]["ApproximateNumberOfMessages"])

    return queue_length


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler for getting SQS and ECS status."""
    try:
        logger.info(f"Getting status of ECS cluster {ECS_CLUSTER_NAME}")
        ecs_status = get_ecs_status(
            cluster_name=ECS_CLUSTER_NAME,
            task_family_name=ECS_TASK_FAMILY_NAME,
        )
        queue_length = get_queue_length(SQS_QUEUE_URL)

        # Return success response
        response = {
            "ecs_status": ecs_status,
            "queue_length": queue_length,
        }
        return create_response(200, response)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
