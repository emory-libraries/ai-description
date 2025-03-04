# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Authorize user."""
import hashlib
import hmac
import os
import time
from typing import Any

import boto3

# Constants
SECRET_NAME = os.environ["SECRET_NAME"]
AWS_REGION = os.environ["AWS_REGION"]

# Initialize AWS clients
secrets_manager = boto3.client("secretsmanager", region_name=AWS_REGION)


def get_secret(secret_name: str) -> str:
    """Get secret."""
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except Exception as e:
        print(f"Error retrieving secret: {str(e)}")
        raise


def verify_token(token: str, secret: str) -> bool:
    """Verify token."""
    try:
        parts = token.split(".")
        if len(parts) != 4:
            return False

        username, random_part, expiration, signature = parts

        # Check if token has expired
        if int(expiration) < int(time.time()):
            return False

        # Verify signature
        message = f"{username}.{random_part}.{expiration}"
        expected_signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

        if signature != expected_signature:
            return False

        return True
    except Exception:
        return False


def generate_policy(principal_id: str, effect: str, resource: str) -> dict[str, Any]:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}],
        },
    }


def lambda_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Lambda handler."""
    token = event["authorizationToken"]

    secret = get_secret(SECRET_NAME)

    if verify_token(token, secret):
        return generate_policy("user", "Allow", event["methodArn"])
    else:
        raise Exception("Unauthorized")
