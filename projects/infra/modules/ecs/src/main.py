# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""ECS worker script for processing batch jobs."""

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from image_captioning_assistant.generate.bias_analysis.generate_work_bias_analysis import generate_work_bias_analysis
from image_captioning_assistant.generate.generate_structured_metadata import (
    DocumentLengthError,
    generate_work_structured_metadata,
)

AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
UPLOADS_BUCKET_NAME = os.environ["UPLOADS_BUCKET_NAME"]
S3_CONFIG = Config(
    s3={"addressing_style": "virtual"},
    signature_version="s3v4",
)
S3_KWARGS = {
    "config": S3_CONFIG,
    "region_name": AWS_REGION,
}
LLM_KWARGS = {
    "region_name": AWS_REGION,
    "config": Config(
        retries={"max_attempts": 1, "mode": "standard"},
    ),
}
RESIZE_KWARGS = {
    "max_dimension": 2048,
    "jpeg_quality": 95,
}
JOB_NAME = "job_name"
JOB_TYPE = "job_type"
WORK_ID = "work_id"
IMAGE_S3_URIS = "image_s3_uris"
CONTEXT_S3_URI = "context_s3_uri"
ORIGINAL_METADATA_S3_URI = "original_metadata_s3_uri"
WORK_STATUS = "work_status"

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

s3 = boto3.client("s3", config=S3_CONFIG, region_name=AWS_REGION)
sqs = boto3.client("sqs", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(WORKS_TABLE_NAME)


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
            except Exception as e:
                uri = future_to_uri[future]
                logger.error(f"Error processing {uri}: {e}")

    # Remove any duplicates (in case folders overlapped)
    return list(dict.fromkeys(all_files))


def update_dynamodb_item(job_name, work_id, update_data):
    status = "READY FOR REVIEW"
    try:
        update_expression = "SET #status = :status"
        expression_attribute_names = {"#status": WORK_STATUS}
        expression_attribute_values = {":status": status}

        for key, value in update_data.items():
            update_expression += f", #{key} = :{key}"
            expression_attribute_names[f"#{key}"] = key
            expression_attribute_values[f":{key}"] = value

        table.update_item(
            Key={JOB_NAME: job_name, WORK_ID: work_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )
        logger.info(f"Updated DynamoDB item for job={job_name}, work={work_id} to {status}")
    except ClientError as e:
        logger.error(f"Failed to update DynamoDB for job={job_name}, work={work_id}: {str(e)}")


def update_dynamodb_status(job_name, work_id, status):
    try:
        table.update_item(
            Key={JOB_NAME: job_name, WORK_ID: work_id},
            UpdateExpression=f"SET {WORK_STATUS} = :status",
            ExpressionAttributeValues={":status": status},
        )
        logger.info(f"Updated DynamoDB item for job={job_name}, work={work_id} to {status}")
    except ClientError as e:
        logger.error(f"Failed to update DynamoDB for job={job_name}, work={work_id}: {str(e)}")


def process_sqs_messages():
    """Process SQS messages."""
    while True:
        # Receive message from SQS queue
        logging.info("Retrieving messages from SQS queue")
        response = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            AttributeNames=["All"],
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
            VisibilityTimeout=600,
            WaitTimeSeconds=0,
        )
        logging.info("Retrieved messages from SQS queue")

        # Check if there are any messages
        if "Messages" not in response:
            logger.info("No more messages in the queue.")
            sys.exit()

        for message in response["Messages"]:
            try:
                # Parse the message body
                message_body = json.loads(message["Body"])
                job_name = message_body[JOB_NAME]
                job_type = message_body[JOB_TYPE]
                work_id = message_body[WORK_ID]
                context_s3_uri = message_body[CONTEXT_S3_URI]
                image_s3_uris = expand_s3_uris_to_files(message_body[IMAGE_S3_URIS])
                original_metadata_s3_uri = message_body[ORIGINAL_METADATA_S3_URI]

                logger.info(f"Message Body: {message_body}")
                logger.info(f"Job name: {job_name}")
                logger.info(f"Job type: {job_type}")
                logger.info(f"Work ID: {work_id}")
                logger.info(f"Context S3 URI: {context_s3_uri}")
                logger.info(f"Image S3 URIs: {image_s3_uris}")
                logger.info(f"Original metadata S3 URI: {original_metadata_s3_uri}")

                # Update work_status for the item in DynamoDB to "IN PROGRESS"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="IN PROGRESS")

                if job_type == "metadata":
                    work_structured_metadata = generate_work_structured_metadata(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    work_bias_analysis = generate_work_bias_analysis(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        original_metadata_s3_uri=original_metadata_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    # Update DynamoDB with the bias_analysis field
                    update_data = work_structured_metadata.model_dump() | work_bias_analysis.model_dump()
                    update_dynamodb_item(
                        job_name=job_name,
                        work_id=work_id,
                        update_data=update_data,
                    )
                elif job_type == "bias":
                    work_bias_analysis = generate_work_bias_analysis(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        original_metadata_s3_uri=original_metadata_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    # Update DynamoDB with the bias_analysis field
                    update_dynamodb_item(
                        job_name=job_name,
                        work_id=work_id,
                        update_data=work_bias_analysis.model_dump(),
                    )
                else:
                    raise ValueError(f"{JOB_TYPE}='{job_type}' not supported")

                # Delete the message from the queue
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
            except Exception as exc:
                if isinstance(exc, DocumentLengthError):
                    # If it's a document length issue, remove from the queue, we don't intend to handle it
                    logger.warning(f"Message {message['MessageId']} failed with error {str(exc)}")
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
                else:
                    logger.exception(f"Message {message['MessageId']} failed with error {str(exc)}")

                # Parse the message body
                message_body = json.loads(message["Body"])
                job_name = message_body[JOB_NAME]
                work_id = message_body[WORK_ID]

                # Update work_status for the item in DynamoDB to "FAILED TO PROCESS"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="FAILED TO PROCESS")


if __name__ == "__main__":
    process_sqs_messages()
