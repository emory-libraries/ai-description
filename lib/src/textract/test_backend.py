# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import asyncio
import os
import sys

import boto3
from aiobotocore.session import get_session
from botocore.config import Config
from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
poppler_bin = os.path.join(current_dir, "resources", "poppler", "Library", "bin")
sys.path.insert(0, src_dir)
os.environ["PATH"] += os.pathsep + poppler_bin

from src.semsTextract import TextractExtractor

logger.remove()
logger.add(sys.stderr, level="DEBUG")

my_config = Config(region_name="us-east-1", signature_version="v4", retries={"max_attempts": 10, "mode": "standard"})


async def main():
    # Verify Poppler path
    logger.debug(f"Poppler path: {os.environ['PATH']}")

    session = get_session()
    async with session.create_client("s3", config=my_config) as s3_client, session.create_client(
        "textract", config=my_config
    ) as textract_client:

        current_region = boto3.session.Session().region_name
        logger.info(f"Current AWS region: {current_region}")

        bucket_name = "bucket"
        key = "file"

        extractor = TextractExtractor()
        try:
            result = await extractor.extract(bucket=bucket_name, key=key)
            logger.info(f"Extraction result: {result}")
        except Exception as e:
            logger.exception("Error during extraction")


if __name__ == "__main__":
    asyncio.run(main())
