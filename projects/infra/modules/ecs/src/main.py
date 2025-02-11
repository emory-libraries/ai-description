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

AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
UPLOADS_BUCKET_NAME = os.environ["UPLOADS_BUCKET_NAME"]
S3_CONFIG = Config(
    s3={"addressing_style": "virtual"},
    signature_version="s3v4",
)

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


def update_dynamodb_status(job_name, work_id, status):
    try:
        table.update_item(
            Key={"job_name": job_name, "work_id": work_id},
            UpdateExpression="SET work_status = :status",
            ExpressionAttributeValues={":status": status},
        )
        logger.info(f"Updated DynamoDB item for job={job_name}, work={work_id} to {status}")
    except ClientError as e:
        logger.error(f"Failed to update DynamoDB for job={job_name}, work={work_id}: {str(e)}")


def process_sqs_messages():
    # Create SQS client

    while True:
        # Receive message from SQS queue
        logging.info("Retrieving message from SQS queue")
        response = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            AttributeNames=["All"],
            MaxNumberOfMessages=1,
            MessageAttributeNames=["All"],
            VisibilityTimeout=30,
            WaitTimeSeconds=0,
        )

        # Check if there are any messages
        if "Messages" not in response:
            logger.info("No more messages in the queue.")
            break

        for message in response["Messages"]:
            try:

                # Parse the message body
                message_body = json.loads(message["Body"])
                job_name = message_body["job_name"]
                work_id = message_body["work_id"]

                # Update work_status for the item in DynamoDB to "PROCESSING"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="PROCESSING")

                # Processing the message will eventually go here
                logger.info(f"Message Body: {message_body}")
                logger.info(f"Job name: {job_name}")
                logger.info(f"Work ID: {work_id}")

                # Update work_status for the item in DynamoDB to "READY FOR REVIEW"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="READY FOR REVIEW")

                # Delete the message from the queue
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])
            except Exception as exc:
                logger.warning(f"Message {message['MessageId']} failed with error {str(exc)}")

                # Parse the message body
                message_body = json.loads(message["Body"])
                job_name = message_body["job_name"]
                work_id = message_body["work_id"]

                # Update work_status for the item in DynamoDB to "FAILED TO PROCESS"
                update_dynamodb_status(job_name=job_name, work_id=work_id, status="FAILED TO PROCESS")


if __name__ == "__main__":
    process_sqs_messages()
