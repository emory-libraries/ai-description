# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""ECS worker script for processing batch jobs."""
import json
import logging
import os
import sys

import boto3

AWS_REGION = os.environ["AWS_REGION"]
UPLOADS_BUCKET_NAME = os.environ["UPLOADS_BUCKET_NAME"]
RESULTS_BUCKET_NAME = os.environ["RESULTS_BUCKET_NAME"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def process_sqs_messages():
    # Create SQS client
    sqs = boto3.client("sqs", region_name=AWS_REGION)

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
            # Process the message
            logger.info(f"Message Body: {message['Body']}")

            # If the message body is JSON, you can parse and print it more nicely
            try:
                body = json.loads(message["Body"])
                logger.info(f"Parsed Message Body: {json.dumps(body, indent=2)}")
            except json.JSONDecodeError:
                pass  # Not JSON, already printed as string

            logger.info(f"Message ID: {message['MessageId']}")
            logger.info(f"Receipt Handle: {message['ReceiptHandle']}")
            logger.info("Attributes:")
            for key, value in message.get("Attributes", {}).items():
                print(f"  {key}: {value}")
            logger.info("Message Attributes:")
            for key, value in message.get("MessageAttributes", {}).items():
                logger.info(f"  {key}: {value['StringValue']}")
            logger.info("\n")

            # Delete the message from the queue
            sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])


if __name__ == "__main__":
    process_sqs_messages()
