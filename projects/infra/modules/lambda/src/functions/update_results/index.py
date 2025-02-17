# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Update Results handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
WORKS_TABLE_NAME = os.environ["WORKS_TABLE_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}
JOB_NAME = "job_name"
WORK_ID = "work_id"
WORK_STATUS = "work_status"

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(WORKS_TABLE_NAME)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

deserializer = TypeDeserializer()


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal type serialization."""

    def default(self, obj: Any) -> Any:
        """Default method."""
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler."""
    try:
        # Parse the request body
        body = json.loads(event["body"])
        job_name = body.get(JOB_NAME)
        work_id = body.get(WORK_ID)
        updated_fields = body.get("updated_fields")

        if not job_name or not work_id or not updated_fields:
            logger.error("Missing required parameters")
            return create_response(400, {"error": "Missing required parameters"})

        # Prepare the update expression and attribute values
        update_expression = "SET "
        expression_attribute_values = {}
        expression_attribute_names = {}

        for key, value in updated_fields.items():
            update_expression += f"#{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value
            expression_attribute_names[f"#{key}"] = key

        # Remove the trailing comma and space
        update_expression = update_expression[:-2]

        # Update the item in DynamoDB
        response = table.update_item(
            Key={JOB_NAME: job_name, WORK_ID: work_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW",
        )

        updated_item = response.get("Attributes")
        if updated_item:
            logger.info(f"Successfully updated item for {JOB_NAME}={job_name} and {WORK_ID}={work_id}")
            return create_response(200, {"message": "Item updated successfully", "item": updated_item})
        else:
            logger.warning(f"No item found for {JOB_NAME}={job_name} and {WORK_ID}={work_id}")
            return create_response(404, {"error": "Item not found"})

    except ClientError as e:
        logger.error(f"AWS service error: {e}")
        return create_response(500, {"error": "Internal server error"})
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return create_response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_response(500, {"error": "Internal server error"})
