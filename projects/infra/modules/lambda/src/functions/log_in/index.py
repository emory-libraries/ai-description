# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Log in."""

import base64
import json
import logging
import os
import time
import datetime
import secrets
from decimal import Decimal
from typing import Any
import hmac
import hashlib

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Constants
AWS_REGION = os.environ["AWS_REGION"]
ACCOUNTS_TABLE_NAME = os.environ["ACCOUNTS_TABLE_NAME"]
SECRET_NAME = os.environ["SECRET_NAME"]
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Credentials": True,
}

# Initialize AWS clients globally
secrets_manager = boto3.client("secretsmanager", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(ACCOUNTS_TABLE_NAME)
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


def get_secret(secret_name: str) -> str:
    """Get secret."""
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(str(e))
        raise e
    else:
        if "SecretString" in response:
            return response["SecretString"]
        else:
            return base64.b64decode(response["SecretBinary"])


def create_response(status_code: int, body: Any) -> dict[str, Any]:
    """Create a standardized API response."""
    return {
        "statusCode": status_code,
        "body": json.dumps(body, cls=DecimalEncoder),
        "headers": CORS_HEADERS,
    }

def generate_token(username: str, secret: str) -> str:
    """Generate a secure token."""
    secret_dict = json.loads(secret)
    secret_key = secret_dict.get("token_secret", "")
    
    # Generate a secure random token
    random_part = secrets.token_hex(16)
    # Add an expiration time (e.g., 1 hour from now)
    expiration = int(time.time()) + 3600
    
    # Combine parts
    token_parts = f"{username}.{random_part}.{expiration}"
    
    # Create a signature using the secret
    signature = hmac.new(secret_key.encode(), token_parts.encode(), hashlib.sha256).hexdigest()
    
    # Combine all parts
    return f"{token_parts}.{signature}"


def handler(event: Any, context: Any) -> dict[str, Any]:
    """Lambda handler."""
    # Load args from event
    body = json.loads(event["body"])
    # Get username and password from the event
    for key in ("username", "password"):
        if key not in body:
            return create_response(400, {"Error": f"{key} not found in request"})

    username = body["username"]
    password = body["password"]

    try:
        # Query the DynamoDB table for the given username
        response = table.query(KeyConditionExpression=Key("username").eq(username))

        # Check if the user exists and the password matches
        if response["Items"]:
            stored_password = response["Items"][0]["password"]
            if stored_password == password:
                # Generate JWT
                secret = get_secret(SECRET_NAME)
                session_token = generate_token(username=username, secret=secret)
                return create_response(200, {"sessionToken": session_token})

        return create_response(401, {"Error": "Invalid username or password"})

    except Exception as e:
        return create_response(500, {"Error": str(e)})
