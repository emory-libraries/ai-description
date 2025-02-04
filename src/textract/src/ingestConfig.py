from typing import List
from pydantic import Field

from config import BaseConfig, BaseProcessingConfig, BaseStorageConfig

class ProcessingConfig(BaseProcessingConfig):
    """Processing configuration."""

    max_polling_time: int = Field(
        default=600,
        validation_alias="MAX_POLLING_TIME",
        description="Maximum time in seconds to wait for Textract processing",
    )
    textract_feature_types: List[str] = Field(
        default=["FORMS", "TABLES", "SIGNATURES", "LAYOUT"],
        description="AWS Textract feature types to extract from documents",
    )

class StorageConfig(BaseStorageConfig):
    """Storage configuration."""

    textract_bucket_name: str = Field(
        default="emory-testui", 
        validation_alias="TEXTRACT_BUCKET_NAME", 
        description="Name of the S3 bucket for Textract results"
    )

class IngestConfig(BaseConfig):
    """Main configuration."""

    processing: ProcessingConfig = Field(
        default_factory=ProcessingConfig, 
        description="Configuration for document processing"
    )
    storage: StorageConfig = Field(
        default_factory=StorageConfig, 
        description="Configuration for storage services"
    )

ingest_config = IngestConfig()

if __name__ == "__main__":
    print(ingest_config.model_dump())