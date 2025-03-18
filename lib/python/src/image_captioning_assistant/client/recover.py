# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

JOB_NAME = "job_name"
WORK_ID = "work_id"
WORK_STATUS = "work_status"
IN_QUEUE = "IN QUEUE"
FAILED_TO_PROCESS = "FAILED TO PROCESS"


def send_to_sqs(items: list, queue_url: str) -> int:
    """
    Send job_name and work_id from each item to SQS queue

    Args:
        items (list): List of DynamoDB items to process
        queue_url (str): URL of the SQS queue

    Returns:
        int: Number of successfully queued items
    """
    successful_count = 0

    for item in items:
        # Extract required fields
        job_name = item.get(JOB_NAME)
        work_id = item.get(WORK_ID)

        if not job_name or not work_id:
            logger.warning(f"Skipping item missing required fields: {item}")
            continue

        message_body = {JOB_NAME: job_name, WORK_ID: work_id}

        try:
            # Send message to SQS queue
            response = sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
            successful_count += 1
            logger.info(f"Message sent to SQS: {message_body}, MessageId: {response.get('MessageId')}")

        except ClientError as e:
            logger.error(f"Error sending message to SQS: {e}")

    return successful_count


def get_items_with_status(status: str, table: Any) -> list:
    """
    Get all items with the specified work_status

    Args:
        status (str): The work_status to filter for
        table (dynamodb.Table) The table to search

    Returns:
        list: Items with the specified work_status
    """
    items = []
    last_evaluated_key = None

    logger.info(f"Scanning table: {table.name} for items with status '{status}'")

    while True:
        scan_kwargs = {"FilterExpression": boto3.dynamodb.conditions.Attr(WORK_STATUS).eq(status)}

        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = table.scan(**scan_kwargs)
        current_items = response.get("Items", [])
        items.extend(current_items)

        logger.info(f"Scan batch returned {len(current_items)} items with status '{status}'")
        if current_items and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Sample item: {current_items[0]}")

        last_evaluated_key = response.get("LastEvaluatedKey")

        if not last_evaluated_key:
            break

    logger.info(f"Found total of {len(items)} items with work_status '{status}'")
    return items


def change_status(from_status: str, to_status: str, table: Any) -> int:
    """
    Change items from one status to another status

    Args:
        from_status (str): The current status to find items by
        to_status (str): The new status to set for matching items
        table (Any): DynamoDB table.

    Returns:
        int: Number of items successfully updated
    """
    # Get items with the specified status
    items = get_items_with_status(status=from_status, table=table)

    if not items:
        logger.info(f"No items found with status '{from_status}'")
        return 0

    # Update each item's status
    updated_count = 0
    for item in items:
        job_name = item.get(JOB_NAME)
        work_id = item.get(WORK_ID)

        if not job_name or not work_id:
            logger.warning(f"Skipping item missing required fields: {item}")
            continue

        try:
            table.update_item(
                Key={JOB_NAME: job_name, WORK_ID: work_id},
                UpdateExpression="SET work_status = :new_status",
                ExpressionAttributeValues={":new_status": to_status, ":old_status": from_status},
                ConditionExpression=f"{WORK_STATUS} = :old_status",
            )
            updated_count += 1
            logger.info(f"Updated item status from '{from_status}' to '{to_status}': {job_name}/{work_id}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(f"Item status changed since scan: {job_name}/{work_id}")
            else:
                logger.error(f"Error updating item: {e}")

    logger.info(f"Updated {updated_count} items from '{from_status}' to '{to_status}'")
    return updated_count


def queue_items_with_status(status: str, queue_url: str, table: Any) -> int:
    """
    Add all items with a specific status to SQS queue

    Args:
        status (str): The work_status of items to queue
        queue_url (str): URL of the SQS queue
        table (Any): DynamoDB table.

    Returns:
        int: Number of items successfully added to SQS
    """
    # Get items with the specified status
    items = get_items_with_status(status=status, table=table)

    if not items:
        logger.info(f"No items found with status '{status}' to queue")
        return 0

    # Send items to SQS
    successful_count = send_to_sqs(items, queue_url)
    logger.info(f"Added {successful_count} items with status '{status}' to SQS queue")

    return successful_count


def process_orphaned_items(orphaned_status: str, table: Any):
    """
    Find items with work_status == 'FAILED TO PROCESS',
    update them to 'IN QUEUE', and send them to SQS
    """
    try:
        # Change items from orphaned_status to 'IN QUEUE'
        updated_count = change_status(
            from_status=orphaned_status,
            to_status=IN_QUEUE,
            table=table,
        )

        # Queue all items with 'IN QUEUE' status
        queued_count = queue_items_with_status(
            status=IN_QUEUE,
            queue_url=queue_url,
            table=table,
        )

        logger.info(f"Summary: {updated_count} items updated to '{IN_QUEUE}', {queued_count} items sent to SQS")
        return updated_count, queued_count

    except Exception as e:
        logger.error(f"Error processing items: {e}")
        return 0, 0


# Execute the function
if __name__ == "__main__":
    table = dynamodb.Table("ai-description-dev-nt01-works-table")
    queue_url = "https://sqs.us-east-1.amazonaws.com/008971633436/ai-description-dev-nt01-queue"
    orphan_status = FAILED_TO_PROCESS

    updated_items, queued_items = process_orphaned_items(
        orphaned_status=orphan_status,
        table=table,
    )
    print(f"Updated {updated_items} items from '{orphan_status}' to '{IN_QUEUE}'")
    queue_items_with_status(
        status=IN_QUEUE,
        queue_url=queue_url,
        table=table,
    )
    print(f"Successfully queued {queued_items} items to SQS")
