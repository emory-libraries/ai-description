# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AwsConfig(BaseSettings):
    """AWS service configuration."""

    region: str = Field(
        default="us-east-1", validation_alias="AWS_REGION", description="AWS region where services are deployed"
    )


class BaseProcessingConfig(BaseSettings):
    """Base processing configuration."""

    max_retries: int = Field(
        default=10,
        ge=0,
        validation_alias="MAX_RETRIES",
        description="Maximum number of retry attempts for failed operations",
    )
    max_retry_timeout: int = Field(
        default=300.0,
        ge=0.0,
        validation_alias="MAX_RETRY_TIMEOUT",
        description="Maximum timeout in seconds between retry attempts",
    )


class BaseStorageConfig(BaseSettings):
    """Base storage configuration."""


class BaseConfig(BaseSettings):
    """Base configuration."""

    aws: AwsConfig = Field(default_factory=AwsConfig, description="AWS service configuration settings")


base_config = BaseConfig()
