# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from typing import Any

import boto3
from botocore.exceptions import ClientError
from loguru import logger


def list_contents_of_folder(
    bucket: str,
    prefix: str,
    s3_client_kwargs: dict[str, Any],
) -> list[str]:
    """List the contents of folder on S3.

    Args:
        bucket (str): Name of S3 bucket.
        prefix (str): Folder path.

    Returns:
        list[str]: Keys of elements under prefix.
    """
    if not prefix.endswith("/"):
        prefix += "/"
    logger.info(f"s3_client_kwargs: {s3_client_kwargs}")
    client = boto3.client("s3", **s3_client_kwargs)
    response = client.list_objects(
        Bucket=bucket,
        Prefix=prefix,
    )
    logger.debug(f"list_conents_of_folder response: {response}")
    return [obj["Key"] for obj in response["Contents"]]


def load_to_bytes(
    s3_bucket: str,
    s3_key: str,
    s3_client_kwargs: dict[str, Any],
) -> bytes:
    """Load bytes directly into memory."""
    try:
        s3_client = boto3.client("s3", **s3_client_kwargs)
        file_bytes = s3_client.get_object(
            Bucket=s3_bucket,
            Key=s3_key,
        )["Body"].read()
        return file_bytes
    except Exception as exc:
        logger.warning(f"Failed to load {s3_key} from {s3_bucket}")
        raise exc

def load_to_str(
    s3_bucket: str,
    s3_key: str,
    s3_client_kwargs: dict[str, Any],
    encoding: str = "utf-8",
) -> str:
    """Load a plain-text file into string."""
    file_bytes = load_to_bytes(
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        s3_client_kwargs=s3_client_kwargs,
    )
    return file_bytes.decode(encoding)


def copy_s3_object(source_bucket: str, source_key: str, dest_bucket: str, dest_key: str):
    """Copy an object from one S3 location to another."""
    s3_client = boto3.client("s3")

    try:
        # Construct the source dictionary
        copy_source = {"Bucket": source_bucket, "Key": source_key}

        # Copy the object
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)

        print(f"Object copied from s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}")
        return True

    except ClientError as e:
        print(f"Error copying object: {e}")
        return False
