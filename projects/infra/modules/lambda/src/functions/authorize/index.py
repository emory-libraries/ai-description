# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Constants
SECRET_NAME = os.environ.get("SECRET_NAME")
AWS_REGION = os.environ.get("AWS_REGION")

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not SECRET_NAME or not AWS_REGION:
    raise ValueError("SECRET_NAME and AWS_REGION must be set in environment variables")

# Initialize AWS clients
secrets_manager = boto3.client("secretsmanager", region_name=AWS_REGION)

# Cache for the secret
secret_cache = {"value": None, "last_fetched": 0}
SECRET_CACHE_TTL = 300  # 5 minutes


def get_secret(secret_name: str) -> str:
    """Get secret with caching."""
    current_time = time.time()
    if secret_cache["value"] is None or current_time - secret_cache["last_fetched"] > SECRET_CACHE_TTL:
        try:
            response = secrets_manager.get_secret_value(SecretId=secret_name)
            secret_cache["value"] = response["SecretString"]
            secret_cache["last_fetched"] = current_time
        except ClientError as e:
            logging.error(f"Error retrieving secret: {e}")
            raise
    return secret_cache["value"]


def verify_token(token: str, secret: str) -> bool:
    """Verify token."""
    try:
        parts = token.split(".")
        if len(parts) != 4:
            logging.error(f"Invalid token format. Expected 4 parts, got {len(parts)}")
            return False

        username, random_part, expiration, signature = parts

        logging.info(f"Verifying token for user: {username}")
        logging.info(f"Token expiration: {expiration}")
        logging.info(f"Current time: {int(time.time())}")

        # Check if token has expired
        if int(expiration) < int(time.time()):
            logging.warning("Token has expired")
            return False

        # Verify signature
        message = f"{username}.{random_part}.{expiration}"
        expected_signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        if signature != expected_signature:
            logging.error("Invalid signature")
            return False

        logging.info("Token successfully verified")
        return True
    except Exception as e:
        logging.exception(f"Error verifying token: {e}")
        return False


def generate_policy(principal_id: str, effect: str, method_arn: str) -> dict[str, Any]:
    """Generate policy."""
    # Extract the API ID, stage, and account ID from the method ARN
    tmp = method_arn.split(":")
    api_gateway_arn_tmp = tmp[5].split("/")
    aws_account_id = tmp[4]
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": f"arn:aws:execute-api:{AWS_REGION}:{aws_account_id}:{api_gateway_arn_tmp[0]}/*/*",
                }
            ],
        },
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler."""
    logging.info(f"Event: {json.dumps(event)}")  # Log the event for debugging

    token = event.get("authorizationToken")
    if token and token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
    method_arn = event["methodArn"]
    if not token:
        logging.warning("No authorization token provided")
        return generate_policy("user", "Deny", method_arn)

    try:
        secret = get_secret(SECRET_NAME)
    except Exception as e:
        logging.exception(f"Failed to retrieve secret: {e}")
        return generate_policy("user", "Deny", method_arn)

    if verify_token(token, secret):
        return generate_policy("user", "Allow", method_arn)
    else:
        return generate_policy("user", "Deny", method_arn)
