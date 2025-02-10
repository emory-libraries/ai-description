# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from pathlib import Path

from botocore.config import Config
from image_captioning_assistant.aws.s3 import list_contents_of_folder, load_image_bytes
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.tables.document import put_document
from image_captioning_assistant.data.db.tables.document_bias import (
    clear_document_bias_by_job_and_document,
    create_document_bias,
)
from image_captioning_assistant.data.db.tables.document_metadata import (
    create_document_metadata,
    delete_document_metadata_by_id_and_job,
    get_document_metadata_by_id_and_job,
)
from image_captioning_assistant.generate.generate_structured_metadata import (
    generate_structured_metadata,
    StructuredMetadata,
)
from loguru import logger
from tqdm import tqdm


def process_job(
    batch_job_name: str,
    s3_bucket: str,
    s3_prefix: str,
    db_manager: DatabaseManager,
    aws_region: str,
    skip_completed: bool = False,
) -> None:
    """Process folder of S3 images.

    Args:
        batch_job_name (str): Unique name of the batch job.
        s3_bucket (str): Bucket where input files are stored.
        s3_prefix (str): Prefix where input files are stored.
        db_manager (DatabaseManager): Client for interacting with DB.
        aws_region (str): Region where services are located.
        skip_completed (bool): Whether or not to skip processing items
            with existing results under the same job name.

    boto3.client("s3", **{"region_name":"us-east-1", "config": Config({})})
    """
    s3_kwargs = {
        "config": Config(
            s3={"addressing_style": "virtual"},
            signature_version="s3v4",
        ),
        "region_name": aws_region,
    }
    for image_key in tqdm(list_contents_of_folder(bucket=s3_bucket, prefix=s3_prefix, s3_client_kwargs=s3_kwargs)):
        try:
            if Path(image_key).suffix.lower() not in [
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".bmp",
            ]:
                logger.info(f"Skipping {image_key} - not a recognized image")
                continue
            document_id = image_key  # TODO: FIX ME
            # See if there are results already
            completed_row = get_document_metadata_by_id_and_job(
                db_manager=db_manager,
                document_id=document_id,
                batch_job_name=batch_job_name,
            )
            # If there are, skip processing the item
            if completed_row and skip_completed:
                continue
            # Otherwise if completed row exists,
            # clear out any existing rows for this document under the same job name
            elif completed_row:
                delete_document_metadata_by_id_and_job(
                    db_manager=db_manager,
                    batch_job_name=batch_job_name,
                    document_id=document_id,
                )
                clear_document_bias_by_job_and_document(
                    db_manager=db_manager,
                    batch_job_name=batch_job_name,
                    document_id=document_id,
                )

            # This table will only be necessary if front/backs are multi-file
            put_document(
                db_manager=db_manager,
                document_id=document_id,
                image_id=image_key,  # TODO: FIX ME
            )
            # For now assume one file one document
            img_bytes = load_image_bytes(s3_bucket, image_key, s3_kwargs)
            # Define kwargs at each loop because generate_structured_metadata involves popping
            llm_kwargs = {
                "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "region_name": aws_region,
            }
            metadata: StructuredMetadata = generate_structured_metadata(
                img_bytes_list=[img_bytes],
                llm_kwargs=llm_kwargs,
                img_context="These belong to the Langmuir collection",
            )
            # Write each potential bias to DB
            for potential_bias in metadata.potential_biases:
                create_document_bias(
                    db_manager=db_manager,
                    batch_job_name=batch_job_name,
                    document_id=document_id,
                    bias_type=potential_bias.bias_type,
                    bias_level=potential_bias.bias_level,
                    explanation=potential_bias.explanation,
                )
            # Write structured metadata to DB
            create_document_metadata(
                db_manager=db_manager,
                batch_job_name=batch_job_name,
                document_id=document_id,
                description=metadata.description,
                transcription=metadata.transcription,
                people_and_groups=metadata.people_and_groups,
                date=metadata.date,
                location=metadata.location,
                publication_info=metadata.publication_info,
                contextual_info=metadata.contextual_info,
            )
        except Exception as exc:
            logger.exception(f"Error handling job='{batch_job_name}' image='{image_key}': {str(exc)}")
            pass
