# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for a work."""

from typing import Any

from cloudpathlib import S3Path
from langchain_aws import ChatBedrockConverse

from image_captioning_assistant.aws.s3 import load_to_str
from image_captioning_assistant.data.data_classes import Metadata
from image_captioning_assistant.generate.structured_metadata.utils import (
    create_messages,
    invoke_with_retry,
    load_and_resize_images,
)


def generate_work_metadata(
    image_s3_uris: str,
    llm_kwargs: dict[str, Any],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    context_s3_uri: str | None = None,
) -> Metadata:
    """Generate structured metadata for a work."""
    # Establish a default model
    if "model_id" not in llm_kwargs:
        llm_kwargs["model_id"] = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    work_context = None
    # If context was provided
    if context_s3_uri:
        # Retrieve it from S3
        s3_path = S3Path(context_s3_uri)
        work_context = load_to_str(
            s3_bucket=s3_path.bucket,
            s3_key=s3_path.key,
            s3_client_kwargs=s3_kwargs,
        )
    # Load and resize image bytes
    img_bytes_list = load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)
    # Create messages
    messages = create_messages(
        img_bytes_list=img_bytes_list,
        work_context=work_context,
    )
    llm = ChatBedrockConverse(**llm_kwargs)
    structured_llm = llm.with_structured_output(Metadata)
    # Invoke model
    return invoke_with_retry(structured_llm, messages)
