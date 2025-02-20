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

from image_captioning_assistant.generate.bias_analysis.generate_work_bias_analysis import generate_work_bias_analysis
from image_captioning_assistant.generate.generate_structured_metadata import generate_work_structured_metadata

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
    "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
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


def update_dynamodb_item(job_name, work_id, update_data):
    try:
        update_expression = "SET #status = :status"
        expression_attribute_names = {"#status": WORK_STATUS}
        expression_attribute_values = {":status": "READY FOR REVIEW"}

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
        logger.info(f"Updated DynamoDB item for job={job_name}, work={work_id}")
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
                image_s3_uris = message_body[IMAGE_S3_URIS]
                original_metadata_s3_uri = message_body[ORIGINAL_METADATA_S3_URI]

                logger.info(f"Message Body: {message_body}")
                logger.info(f"Job name: {job_name}")
                logger.info(f"Job type: {job_type}")
                logger.info(f"Work ID: {work_id}")
                logger.info(f"Context S3 URI: {context_s3_uri}")
                logger.info(f"Image S3 URIs: {image_s3_uris}")
                logger.info(f"Original metadata S3 URI: {original_metadata_s3_uri}")

                # Update work_status for the item in DynamoDB to "PROCESSING"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="PROCESSING")

                if job_type == "metadata":
                    work_structured_metadata = generate_work_structured_metadata(
                        image_s3_uris=image_s3_uris,
                        context_s3_uri=context_s3_uri,
                        original_metadata_s3_uri=original_metadata_s3_uri,
                        llm_kwargs=LLM_KWARGS,
                        s3_kwargs=S3_KWARGS,
                        resize_kwargs=RESIZE_KWARGS,
                    )
                    # Update DynamoDB with all fields from work_structured_metadata
                    update_dynamodb_item(
                        job_name=job_name,
                        work_id=work_id,
                        update_data=work_structured_metadata.model_dump(),
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
                logger.exception(f"Message {message['MessageId']} failed with error {str(exc)}")

                # Parse the message body
                message_body = json.loads(message["Body"])
                job_name = message_body[JOB_NAME]
                work_id = message_body[WORK_ID]

                # Update work_status for the item in DynamoDB to "FAILED TO PROCESS"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="FAILED TO PROCESS")


if __name__ == "__main__":
    process_sqs_messages()
