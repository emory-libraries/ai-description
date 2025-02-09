# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Start ECS task handler."""

import json
import logging
import os
from typing import Any

import boto3

# Constants
AWS_REGION = os.environ["AWS_REGION"]
ECS_CLUSTER_NAME = os.environ["ECS_CLUSTER_NAME"]
ECS_TASK_DEFINITION_ARN = os.environ["ECS_TASK_DEFINITION_ARN"]
ECS_TASK_FAMILY_NAME = ECS_TASK_DEFINITION_ARN.split("/")[-1].split(":")[0]
SUBNET_IDS = os.environ["ECS_SUBNET_IDS"].split(",")
SECURITY_GROUP_IDS = os.environ["ECS_SECURITY_GROUP_IDS"].split(",")

# Initialize AWS clients globally
ecs_client = boto3.client("ecs", region_name=AWS_REGION)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler."""
    # Check for running tasks
    try:
        running_tasks = ecs_client.list_tasks(
            cluster=ECS_CLUSTER_NAME, family=ECS_TASK_FAMILY_NAME, desiredStatus="RUNNING"
        )

        if running_tasks["taskArns"]:
            message = "A task is already running. No new task will be started."
            logger.warning(message)
            return {
                "statusCode": 400,
                "body": json.dumps({"message": message}),
            }

        # If no task is running, start a new one
        network_configuration = {
            "awsvpcConfiguration": {
                "subnets": SUBNET_IDS,
                "securityGroups": SECURITY_GROUP_IDS,
                "assignPublicIp": "ENABLED",
            }
        }
        overrides = {
            "containerOverrides": [
                {
                    "name": "processing-container",
                    "environment": [{"name": "JOB_ID"}],
                }
            ]
        }
        logger.info(f"Network configuration: {json.dumps(network_configuration, indent=4)}")
        logger.info(f"Overrides: {json.dumps(overrides, indent=4)}")
        logger.info(f"Running task")
        response = ecs_client.run_task(
            cluster=ECS_CLUSTER_NAME,
            taskDefinition=ECS_TASK_DEFINITION_ARN,
            launchType="FARGATE",
            networkConfiguration=network_configuration,
            overrides=overrides,
        )
        message = f"ECS task {response['tasks'][0]['taskArn']} started successfully"
        logger.info(message)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": message}),
        }

    except Exception as e:
        logger.exception(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
