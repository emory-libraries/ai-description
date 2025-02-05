from typing import Any

from botocore.exceptions import ClientError
import boto3
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


def load_image_bytes(
    s3_bucket: str,
    s3_key: str,
    s3_client_kwargs: dict[str, Any],
) -> bytes:
    """Load image bytes."""
    s3_client = boto3.client("s3", **s3_client_kwargs)
    image_bytes = s3_client.get_object(
        Bucket=s3_bucket,
        Key=s3_key,
    )["Body"].read()
    return image_bytes



def copy_s3_object(
    source_bucket: str, source_key: str, dest_bucket: str, dest_key: str
):
    """Copy an object from one S3 location to another.

    NOTE we don't seem to have CopyObject privileges so the less-direct copy_between_buckets
    will be used instead.
    """
    s3_client = boto3.client('s3')

    try:
        # Construct the source dictionary
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }

        # Copy the object
        s3_client.copy_object(CopySource=copy_source, Bucket=dest_bucket, Key=dest_key)

        logger.info(f"Object copied from s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}")
        return True

    except ClientError as e:
        logger.warning(f"Error copying object: {e}")
        return False


def copy_between_buckets(source_bucket, source_key, dest_bucket, dest_key):
    """Copy an object from one S3 bucket to another using GET and PUT operations."""
    s3_client = boto3.client('s3')

    try:
        # Step 1: GET the object from the source bucket
        response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response['Body'].read()

        # Step 2: PUT the object into the destination bucket
        s3_client.put_object(Bucket=dest_bucket, Key=dest_key, Body=file_content)

        logger.info(f"Successfully copied {source_key} from {source_bucket} to {dest_key} in {dest_bucket}")
        return True

    except ClientError as e:
        logger.warning(f"Error copying object: {e}")
        return False