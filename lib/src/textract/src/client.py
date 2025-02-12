# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import asyncio
from typing import Optional

from aiobotocore.client import AioBaseClient
from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from config import base_config
from loguru import logger


class AWSAsyncManager:
    client: Optional[AioBaseClient] = None
    service_name: str = ""
    config: Optional[AioConfig] = None

    async def start(self) -> None:
        logger.debug(f"Initializing {self.service_name} client")
        session = get_session()
        self.client = await session.create_client(
            self.service_name,
            region_name=base_config.aws.region,
            config=self.config,
        ).__aenter__()
        logger.debug(f"{self.service_name} client initialized successfully")

    async def stop(self) -> None:
        if self.client:
            logger.debug(f"Shutting down {self.service_name} client")
            await self.client.__aexit__(None, None, None)
            self.client = None
            logger.debug(f"{self.service_name} client shutdown complete")

    def __call__(self) -> AioBaseClient:
        if self.client is None:
            logger.error(f"{self.service_name} client not initialized")
            raise RuntimeError("Client is not initialized")
        return self.client


class S3Manager(AWSAsyncManager):
    service_name = "s3"
    config = AioConfig(
        s3={
            "addressing_style": "virtual",
            "signature_version": "s3v4",
        }
    )


class TextractManager(AWSAsyncManager):
    """Async manager for Textract service."""

    service_name = "textract"
