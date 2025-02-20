# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

from typing import Any

from langchain_aws import ChatBedrockConverse

from image_captioning_assistant.data.data_classes import WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.utils import create_messages, load_and_resize_images, invoke_with_retry


def find_biases_in_short_work(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    llm_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    work_context: str | None = None,
    original_metadata: str | None = None,
) -> WorkBiasAnalysis:
    """Find biases in one or two images and, optionally, their existing metadata."""
    # Load and resize image bytes
    img_bytes_list = load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)
    # Create messages
    messages = create_messages(
        img_bytes_list=img_bytes_list,
        work_context=work_context,
        original_metadata=original_metadata,
    )
    llm = ChatBedrockConverse(**llm_kwargs)
    structured_llm = llm.with_structured_output(WorkBiasAnalysis)
    # Invoke model
    return invoke_with_retry(structured_llm, messages)
