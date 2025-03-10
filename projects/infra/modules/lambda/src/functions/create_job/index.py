# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Uploads handler."""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from typing import Any, Dict
from urllib.parse import urlparse

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


def s3_path_to_file_list(s3_path_uri, recursive=True) -> list[str]:
    """
    Processes an S3 URI path and returns a list of S3 URIs.
    - If the path is a folder, returns all files within that folder
    - If the path is a file, returns a list containing just that file URI

    Args:
        s3_path_uri (str): The S3 URI (e.g., 's3://bucket-name/folder/' or 's3://bucket-name/file.txt')
        recursive (bool): Whether to list objects recursively in subfolders (default: True)

    Returns:
        list: List of complete S3 URIs
    """
    # Parse the S3 URI
    parsed_uri = urlparse(s3_path_uri)
    if parsed_uri.scheme != "s3":
        raise ValueError(f"Not a valid S3 URI: {s3_path_uri}")

    bucket = parsed_uri.netloc

    # Remove leading slash if present
    key = parsed_uri.path.lstrip("/")

    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Check if the path exists directly as an object (file)
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        # If we get here, it's a file that exists
        return [s3_path_uri]
    except s3_client.exceptions.ClientError as e:
        # If error code is 404, it's not a file, so we'll treat it as a folder
        if e.response["Error"]["Code"] != "404":
            # If there's a different error, re-raise it
            raise

    # If we get here, the path doesn't exist as a direct object, so treat it as a folder
    # Ensure the path ends with a slash to denote a folder
    folder_prefix = key if key.endswith("/") else key + "/"

    result_uris = []

    # Use paginator to handle potentially large numbers of objects
    paginator = s3_client.get_paginator("list_objects_v2")

    # Configure the paginator
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=folder_prefix)

    # Process each page of results
    for page in page_iterator:
        if "Contents" not in page:
            # No objects found with this prefix
            continue

        for obj in page["Contents"]:
            obj_key = obj["Key"]

            # Skip the folder object itself
            if obj_key == folder_prefix:
                continue

            # If not recursive, skip objects in subfolders
            if not recursive and "/" in obj_key.replace(folder_prefix, "", 1):
                continue

            result_uris.append(f"s3://{bucket}/{obj_key}")

    # If no files were found and the original path doesn't end with a slash,
    # it might be a file pattern (like a prefix for filtering)
    if not result_uris and not key.endswith("/"):
        # Try to list objects with the given prefix
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=key)

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                obj_key = obj["Key"]
                result_uris.append(f"s3://{bucket}/{obj_key}")

    return sorted(result_uris)


def expand_s3_uris_to_files(uri_list, recursive=True, max_workers=10):
    """
    Expands a list of mixed S3 URIs (files and/or folders) into a flat list of all file URIs.

    Args:
        uri_list (list): List of S3 URIs (can be files or folders)
        recursive (bool): Whether to include files in subfolders
        max_workers (int): Maximum number of parallel workers for processing

    Returns:
        list: Flat list of all file URIs
    """
    all_files = []

    # Process URIs in parallel for better performance
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map each URI to its expanded file list
        future_to_uri = {executor.submit(s3_path_to_file_list, uri, recursive): uri for uri in uri_list}

        # Collect results as they complete
        for future in future_to_uri:
            try:
                files = future.result()
                all_files.extend(files)
            except Exception as exc:
                uri = future_to_uri[future]
                logger.error(f"Error processing {uri}: {exc}")
                raise exc

    # Remove any duplicates (in case folders overlapped)
    return list(dict.fromkeys(all_files))


def validate_request_body(body: dict[str, Any]) -> None:
    job_keys = (JOB_NAME, JOB_TYPE, WORKS)
    job_keys_present = [key in body for key in job_keys]
    if any(job_keys_present) and not all(job_keys_present):
        msg = f"Request body requires the following keys: {job_keys}. Request body keys received: {body.keys()}"
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
            WORK_ID: work_id,
        }
        sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(sqs_message))
        logger.debug(f"Successfully added job={job_name} work={work_id} to SQS")
        # Put pending work item in DynamoDB
        ddb_work_item = {
            JOB_NAME: job_name,
            JOB_TYPE: job_type,
            WORK_ID: work_id,
            IMAGE_S3_URIS: expand_s3_uris_to_files(image_s3_uris),
            CONTEXT_S3_URI: context_s3_uri,
            ORIGINAL_METADATA_S3_URI: original_metadata_s3_uri,
            WORK_STATUS: "IN QUEUE",
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
