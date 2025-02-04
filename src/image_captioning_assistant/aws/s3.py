from typing import Any

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
