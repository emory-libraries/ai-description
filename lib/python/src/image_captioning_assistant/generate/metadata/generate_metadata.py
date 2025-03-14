# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for a work."""

import logging
from typing import Any

from cloudpathlib import S3Path

from image_captioning_assistant.aws.s3 import load_to_str
from image_captioning_assistant.data.data_classes import Metadata
from image_captioning_assistant.generate.errors import DocumentLengthError
from image_captioning_assistant.generate.metadata.utils import (
    invoke_model_and_process_response,
    prepare_model_invocation,
)
from image_captioning_assistant.generate.utils import (
    initialize_bedrock_runtime,
    load_and_resize_images,
    needs_court_order,
)

logger = logging.getLogger(__name__)


def generate_metadata_from_images(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    work_context: str | None = None,
) -> Metadata:
    """Generate structured metadata for an image using foundation models.

    Args:
        img_bytes_list: List of image bytes (front/back images, max 2 items)
        llm_kwargs: LLM configuration parameters including:
            - model_id: Model ID
            - region_name: (Optional) AWS region override
        work_context: Additional context to assist metadata generation

    Returns:
        Metadata: Structured metadata object

    Raises:
        ValueError: For unsupported model types
        RuntimeError: After 5 failed attempts to parse model output
    """
    # Configure Bedrock client
    model_name = llm_kwargs["model_id"]
    bedrock_runtime = initialize_bedrock_runtime(llm_kwargs)

    court_order = False
    llm_output = ""

    # Retry loop for robustness around structured metadata
    for attempt in range(5):
        try:
            # Prepare invocation parameters
            invoke_params = prepare_model_invocation(
                bedrock_runtime=bedrock_runtime,
                model_name=model_name,
                img_bytes_list=img_bytes_list,
                work_context=work_context,
                court_order=court_order,
            )

            # Invoke model and process response
            return invoke_model_and_process_response(bedrock_runtime, invoke_params)

        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/5 failed: {str(type(e))} : {str(e)}")
            if attempt == 4:
                # Need to raise exception that was thrown for debugging purposes
                raise e

            # Check if we need to use court order in next attempt
            if hasattr(locals(), "llm_output") and needs_court_order(e, llm_output):
                court_order = True

    raise RuntimeError("Failed to parse model output after 5 attempts")


def generate_metadata_from_s3_images(
    image_s3_uris: list[str],
    llm_kwargs: dict[str, Any],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    context_s3_uri: str | None = None,
) -> Metadata:
    """Generate structured metadata for a work.

    Args:
        image_s3_uris: List of S3 URIs for images
        llm_kwargs: LLM configuration parameters
        s3_kwargs: S3 client configuration
        resize_kwargs: Image resize parameters
        context_s3_uri: S3 URI for additional context

    Returns:
        Metadata: Structured metadata object

    Raises:
        DocumentLengthError: If more than 2 images are provided
    """
    # Enforce max length of two
    if len(image_s3_uris) > 2:
        msg = f"Structured metadata only supports documents of 1-2 pages, {len(image_s3_uris)} pages provided."
        logger.warning(msg)
        raise DocumentLengthError(msg)

    # Establish a default model
    if "model_id" not in llm_kwargs:
        llm_kwargs["model_id"] = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

    # Load context if provided
    work_context = None
    if context_s3_uri:
        s3_path = S3Path(context_s3_uri)
        work_context = load_to_str(
            s3_bucket=s3_path.bucket,
            s3_key=s3_path.key,
            s3_client_kwargs=s3_kwargs,
        )

    # Load and resize image bytes
    img_bytes_list = load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)

    # Generate metadata
    return generate_metadata_from_images(
        img_bytes_list=img_bytes_list,
        llm_kwargs=llm_kwargs,
        work_context=work_context,
    )
