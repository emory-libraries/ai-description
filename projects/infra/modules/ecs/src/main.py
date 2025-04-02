# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""ECS worker script for processing batch jobs."""

import json
import logging
import os
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from image_captioning_assistant.generate.bias_analysis.generate_bias_analysis import (
    generate_bias_analysis_from_s3_images,
)
from image_captioning_assistant.generate.metadata.generate_metadata import generate_metadata_from_s3_images

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
READY_FOR_REVIEW = "READY FOR REVIEW"
IN_PROGRESS = "IN PROGRESS"
FAILED_TO_PROCESS = "FAILED TO PROCESS"

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


def get_work_details(job_name: str, work_id: str) -> dict:
    """Get the details of a work item from DynamoDB.

    Args:
        job_name (str): The job name
        work_id (str): The work ID

    Returns:
        dict: Work item details
    """
    try:
        response = table.get_item(Key={JOB_NAME: job_name, WORK_ID: work_id})

        if "Item" not in response:
            raise ValueError(f"No item found for job_name={job_name}, work_id={work_id}")

        return response["Item"]
    except ClientError as e:
        logger.error(f"Error retrieving item from DynamoDB: {e}")
        raise


def update_dynamodb_item(
    job_name: str,
    work_id: str,
    update_data: dict | None = None,
    status: str | None = None,
) -> None:
    """Update a DynamoDB item with new data and/or status.

    Args:
        job_name (str): The job name
        work_id (str): The work ID
        update_data (dict, optional): Dictionary of field-value pairs to update
        status (str, optional): New status to set for the work item
    """
    try:
        # Start with empty update parts
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        # Add status update if provided
        if status is not None:
            update_expression_parts.append("#status = :status")
            expression_attribute_names["#status"] = WORK_STATUS
            expression_attribute_values[":status"] = status

        # Add field updates from update_data if provided
        if update_data:
            for key, value in update_data.items():
                update_expression_parts.append(f"#{key} = :{key}")
                expression_attribute_names[f"#{key}"] = key
                expression_attribute_values[f":{key}"] = value

        # If nothing to update, return early
        if not update_expression_parts:
            logger.warning(f"No updates provided for job={job_name}, work={work_id}")
            return

        # Create the full update expression
        update_expression = "SET " + ", ".join(update_expression_parts)

        # Perform the update
        table.update_item(
            Key={JOB_NAME: job_name, WORK_ID: work_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
        )

        # Log appropriate message based on what was updated
        log_message = f"Updated DynamoDB item for job={job_name}, work={work_id}"
        if status:
            log_message += f" with status '{status}'"
        if update_data:
            fields = list(update_data.keys())
            log_message += f" and fields: {fields}"

        logger.info(log_message)

    except ClientError as e:
        logger.error(f"Failed to update DynamoDB for job={job_name}, work={work_id}: {str(e)}")
        raise


def process_sqs_messages() -> None:
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
                work_id = message_body[WORK_ID]

                # Get work details from DynamoDB instead of SQS message
                work_item = get_work_details(job_name, work_id)

                job_type = work_item[JOB_TYPE]
                context_s3_uri = work_item[CONTEXT_S3_URI]
                image_s3_uris = work_item[IMAGE_S3_URIS]
                original_metadata_s3_uri = work_item[ORIGINAL_METADATA_S3_URI]

                logger.info(f"Job name: {job_name}")
                logger.info(f"Work ID: {work_id}")
                logger.info(f"Job type: {job_type}")
                logger.info(f"Context S3 URI: {context_s3_uri}")
                logger.info(f"Image S3 URIs: {image_s3_uris}")
                logger.info(f"Original metadata S3 URI: {original_metadata_s3_uri}")

                # Update work_status for the item in DynamoDB to "IN PROGRESS"
                update_dynamodb_item(job_name=job_name, work_id=work_id, status=IN_PROGRESS)

                if job_type == "metadata":
                    work_structured_metadata = generate_metadata_from_s3_images(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    work_bias_analysis = generate_bias_analysis_from_s3_images(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        original_metadata_s3_uri=original_metadata_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    # Update DynamoDB with the bias_analysis field
                    update_data = work_structured_metadata.model_dump() | work_bias_analysis.model_dump()
                elif job_type == "bias":
                    work_bias_analysis = generate_bias_analysis_from_s3_images(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        original_metadata_s3_uri=original_metadata_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    update_data = work_bias_analysis.model_dump()
                else:
                    raise ValueError(f"{JOB_TYPE}='{job_type}' not supported")

                # Update DynamoDB and SQS
                update_dynamodb_item(
                    job_name=job_name,
                    work_id=work_id,
                    update_data=update_data,
                    status=READY_FOR_REVIEW,
                )
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
                logger.info(f"Job {job_name} complete and ready for review")
            except Exception as exc:
                logger.exception(f"Message {message['MessageId']} failed with error {str(exc)}")

                # Parse the message body to get the job_name and work_id
                message_body = json.loads(message["Body"])
                job_name = message_body[JOB_NAME]
                work_id = message_body[WORK_ID]

                # Update work_status for the item in DynamoDB to "FAILED TO PROCESS"
                update_dynamodb_item(job_name=job_name, work_id=work_id, status=FAILED_TO_PROCESS)

                # Always delete the message from the queue after handling the failure
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])


if __name__ == "__main__":
    process_sqs_messages()
