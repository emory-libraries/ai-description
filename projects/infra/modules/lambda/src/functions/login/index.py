# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Results handler."""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
ACCOUNT_TABLE_NAME = os.environ["ACCOUNT_TABLE_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(ACCOUNT_TABLE_NAME)

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
    # Get username and password from the event
    for key in ("username", "password"):
        if key not in event:
            return create_response(400, {"Error": f"{key} not found in request"})

    username = event["username"]
    password = event["password"]

    try:
        # Query the DynamoDB table for the given username
        response = table.query(KeyConditionExpression=Key("username").eq(username))

        # Check if the user exists and the password matches
        if response["Items"]:
            stored_password = response["Items"][0]["password"]
            if stored_password == password:
                return create_response(200, "Success")

        return create_response(401, {"Error": "Invalid username or password"})

    except Exception as e:
        return create_response(500, {"Error": str(e)})
