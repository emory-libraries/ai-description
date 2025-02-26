# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Uploads handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any, Dict

import boto3
from boto3.dynamodb.conditions import Key

# Load environment variables
AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
ECS_CLUSTER_NAME = os.environ["ECS_CLUSTER_NAME"]
ECS_TASK_DEFINITION_ARN = os.environ["ECS_TASK_DEFINITION_ARN"]
ECS_TASK_FAMILY_NAME = ECS_TASK_DEFINITION_ARN.split("/")[-1].split(":")[0]
ECS_CONTAINER_NAME = os.environ["ECS_CONTAINER_NAME"]
SUBNET_IDS = os.environ["ECS_SUBNET_IDS"].split(",")
SECURITY_GROUP_IDS = os.environ["ECS_SECURITY_GROUP_IDS"].split(",")

# Configs
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}
RUN_TASK_KWARGS = {
    "cluster": ECS_CLUSTER_NAME,
    "taskDefinition": ECS_TASK_DEFINITION_ARN,
    "launchType": "FARGATE",
    "networkConfiguration": {
        "awsvpcConfiguration": {
            "subnets": SUBNET_IDS,
            "securityGroups": SECURITY_GROUP_IDS,
            "assignPublicIp": "DISABLED",
        }
    },
    "overrides": {
        "containerOverrides": [
            {
                "name": ECS_CONTAINER_NAME,
                "environment": [{"name": "JOB_ID"}],
            }
        ]
    },
}

# Other constants
JOB_NAME = "job_name"
JOB_TYPE = "job_type"
WORKS = "works"
WORK_ID = "work_id"
IMAGE_S3_URIS = "image_s3_uris"
CONTEXT_S3_URI = "context_s3_uri"
ORIGINAL_METADATA_S3_URI = "original_metadata_s3_uri"
WORK_STATUS = "work_status"

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
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


def validate_request_body(body: dict[str, Any]) -> None:
    job_keys = (JOB_NAME, JOB_TYPE, WORKS)
    job_keys_present = [key in body for key in job_keys]
    if any(job_keys_present) and not all(job_keys_present):
        msg = f"Request body requires the following keys: {job_keys}. Request body keys recieved: {body.keys()}"
        logger.warning(msg)
        raise ValueError(msg)


def job_exists(table, job_name: str) -> bool:
    """Check if a job with the given name already exists."""
    response = table.query(KeyConditionExpression=Key(JOB_NAME).eq(job_name), Limit=1)
    return len(response["Items"]) > 0


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def create_ecs_task(run_task_kwargs: dict[str, Any]) -> str:
    """Create an ECS task if one is not already running."""
    # Check for running tasks
    running_tasks = ecs_client.list_tasks(
        cluster=ECS_CLUSTER_NAME, family=ECS_TASK_FAMILY_NAME, desiredStatus="RUNNING"
    )

    if running_tasks["taskArns"]:
        message = "A task is already running. No new task will be started."
        logger.warning(message)
        return message

    # If no task is running, start a new one
    logger.info(f"Running task")
    logger.debug(f"Task kwargs: {json.dumps(run_task_kwargs, indent=4)}")
    response = ecs_client.run_task(**run_task_kwargs)
    message = f"New ECS task {response['tasks'][0]['taskArn']} started successfully"
    logger.info(message)
    return message


def create_job(job_name: str, works: list[dict[str, str]], job_type: str) -> None:
    """Create job in DynamoDB and SQS."""
    table = dynamodb.Table(WORKS_TABLE_NAME)

    # Check if job already exists
    if job_exists(table, job_name):
        msg = f"Job with name '{job_name}' already exists"
        logger.error(msg)
        raise ValueError(msg)

    for work in works:
        work_id: str = work[WORK_ID]
        image_s3_uris: list[str] = work[IMAGE_S3_URIS]
        context_s3_uri: str | None = work.get(CONTEXT_S3_URI, None)
        original_metadata_s3_uri: str | None = work.get(ORIGINAL_METADATA_S3_URI, None)
        # Add work item to SQS queue
        sqs_message = {
            JOB_NAME: job_name,
            JOB_TYPE: job_type,
            WORK_ID: work_id,
            IMAGE_S3_URIS: image_s3_uris,
            CONTEXT_S3_URI: context_s3_uri,
            ORIGINAL_METADATA_S3_URI: original_metadata_s3_uri,
        }
        sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_message))
        logger.debug(f"Successfully added job={job_name} work={work_id} to SQS")
        # Put pending work item in DynamoDB
        ddb_work_item = {
            JOB_NAME: job_name,
            JOB_TYPE: job_type,
            WORK_ID: work_id,
            IMAGE_S3_URIS: image_s3_uris,
            CONTEXT_S3_URI: context_s3_uri,
            ORIGINAL_METADATA_S3_URI: original_metadata_s3_uri,
            WORK_STATUS: "IN_QUEUE",
        }
        table.put_item(Item=ddb_work_item)
        logger.debug(f"Successfully added job={job_name} work={work_id} to DynamoDB")
    logger.info(f"Successfully added all works for job={job_name} to SQS and DynamoDB")


def handler(event: Any, context: Any) -> Dict[str, Any]:
    """Lambda handler."""
    try:
        response_message = {}

        # Load args from event
        body = json.loads(event["body"])

        # Job creation
        if JOB_NAME in body and JOB_TYPE in body and WORKS in body:
            try:
                validate_request_body(body)
                create_job(
                    job_name=body[JOB_NAME],
                    job_type=body[JOB_TYPE],
                    works=body[WORKS],
                )
                response_message["job_creation"] = "Success"
            except ValueError as ve:
                response_message["job_creation"] = f"Failed: {str(ve)}"
            except Exception as e:
                response_message["job_creation"] = f"Failed: Unexpected error - {str(e)}"
        else:
            response_message["job_creation"] = "No job arguments provided"

        # ECS task creation
        try:
            ecs_message = create_ecs_task(RUN_TASK_KWARGS)
            response_message["ecs_task_creation"] = ecs_message
        except Exception as e:
            response_message["ecs_task_creation"] = f"Failed: {str(e)}"

        return create_response(200, response_message)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
