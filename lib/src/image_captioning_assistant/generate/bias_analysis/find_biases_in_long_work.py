# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

from typing import Any

from langchain_aws import ChatBedrockConverse
from loguru import logger

from image_captioning_assistant.data.data_classes import Biases, WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.utils import (
    create_messages,
    invoke_with_retry,
    load_and_resize_image,
)


def find_biases_in_original_metadata(
    original_metadata: str,
    structured_llm: Any,
    work_context: str | None = None,
):
    """Find biases in original metadata."""
    logger.info(f"Analyzing original metadata")
    messages = create_messages(
        img_bytes_list=[],
        work_context=work_context,
        original_metadata=original_metadata,
    )
    return invoke_with_retry(structured_llm, messages)


def find_biases_in_image(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    structured_llm: Any,
    work_context: str | None = None,
):
    """Find biases in an image."""
    logger.info(f"Analyzing {len(image_s3_uris)} images")
    page_biases = []
    for image_s3_uri in image_s3_uris:
        logger.debug(f"Analyzing image {image_s3_uri}")
        resized_img_bytes = load_and_resize_image(
            image_s3_uri=image_s3_uri,
            s3_kwargs=s3_kwargs,
            resize_kwargs=resize_kwargs,
        )
        messages = create_messages(img_bytes_list=[resized_img_bytes], work_context=work_context)
        image_biases = invoke_with_retry(structured_llm, messages)
        page_biases.extend(image_biases)

    return page_biases


def find_biases_in_long_work(
    image_s3_uris: list[str],
    llm_kwargs: dict[str, Any],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    original_metadata: str | None = None,
    work_context: str | None = None,
) -> WorkBiasAnalysis:
    """Find image and metadata biases independently."""
    llm = ChatBedrockConverse(**llm_kwargs)
    structured_llm = llm.with_structured_output(Biases)
    if original_metadata:
        metadata_biases = find_biases_in_original_metadata(
            original_metadata=original_metadata,
            work_context=work_context,
            structured_llm=structured_llm,
        )
    else:
        metadata_biases = []

    page_biases = find_biases_in_image(
        image_s3_uris=image_s3_uris,
        structured_llm=structured_llm,
        resize_kwargs=resize_kwargs,
        s3_kwargs=s3_kwargs,
        work_context=work_context,
    )
    return WorkBiasAnalysis(
        metadata_biases=metadata_biases,
        page_biases=page_biases,
    )
