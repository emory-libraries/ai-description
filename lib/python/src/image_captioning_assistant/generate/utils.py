# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Utilities for LLM generation."""

import json
import logging
from io import BytesIO
from typing import Any

import boto3
from cloudpathlib import S3Path
from PIL import Image
from pydantic_core import ValidationError
from retry import retry

from image_captioning_assistant.aws.s3 import load_to_bytes
from image_captioning_assistant.generate import prompts as p
from image_captioning_assistant.generate.errors import LLMResponseParsingError

logger = logging.getLogger(__name__)


def convert_and_reduce_image(image_bytes: bytes, max_dimension: int = 2048, jpeg_quality: int = 95) -> bytes:
    """Convert and reduce size of image."""
    # Open image and convert to RGB (removes alpha channel if present)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Set maximum dimensions while maintaining aspect ratio
    image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # Optimize JPEG quality and save to buffer
    buffer = BytesIO()
    image.save(
        buffer, format="JPEG", quality=jpeg_quality, optimize=True  # Adjust between 75-95 for quality/size balance
    )

    buffer.seek(0)
    return buffer.read()


def load_and_resize_image(
    image_s3_uri: str,
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
) -> bytes:
    """Load and resize image."""
    s3_path = S3Path(image_s3_uri)
    img_bytes = load_to_bytes(
        s3_bucket=s3_path.bucket,
        s3_key=s3_path.key,
        s3_client_kwargs=s3_kwargs,
    )
    resized_image = convert_and_reduce_image(
        image_bytes=img_bytes,
        **resize_kwargs,
    )
    return resized_image


def load_and_resize_images(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
) -> list[bytes]:
    """Load and resize images."""
    # Load all img bytes into list
    resized_img_bytes_list = []
    for image_s3_uri in image_s3_uris:
        resized_img_bytes = load_and_resize_image(
            image_s3_uri=image_s3_uri,
            s3_kwargs=s3_kwargs,
            resize_kwargs=resize_kwargs,
        )
        resized_img_bytes_list.append(resized_img_bytes)
    return resized_img_bytes_list


@retry(exceptions=Exception, tries=5, delay=10, backoff=2)
def invoke_with_retry(structured_llm: Any, messages: list) -> Any:
    """Invoke LLM with retry."""
    logger.info("Invoking structured LLM...")
    response = structured_llm.invoke(messages)
    logger.info("Invocation successful")
    return response


def format_prompt_for_converse(
    prompt: str, img_bytes_list: list[bytes], assistant_start: str | None = None
) -> list[dict]:
    """Format prompt for Bedrock Converse API.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Bedrock Converse API.
    """
    content = []
    for img_bytes in img_bytes_list:
        img_message = {
            "image": {
                "format": "jpeg",
                "source": {"bytes": img_bytes},
            }
        }
        content.append(img_message)
    content.append({"text": prompt})
    msg_list = [{"role": "user", "content": content}]
    if assistant_start:
        msg_list.append({"role": "assistant", "content": [{"text": assistant_start}]})
    return msg_list


def extract_json_and_cot_from_text(text: str) -> tuple:
    """Extract JSON and chain-of-thought from text."""
    cot, text = text.split(p.COT_TAG_END)
    try:
        return (cot.replace(p.COT_TAG, ""), json.loads(text.strip()))
    except json.JSONDecodeError:
        logger.warning(f"Could not parse {text}")
        raise LLMResponseParsingError("Could not parse and decode JSON output")


def needs_court_order(e: Exception, llm_output: str) -> bool:
    """Determine if we need to use the court order system prompt."""
    if isinstance(e, (LLMResponseParsingError, ValidationError)):
        raw_output = llm_output.split(p.COT_TAG_END)[-1]
        return any(phrase in raw_output.lower() for phrase in ["apologize", "i cannot", "i can't"])
    return False


def initialize_bedrock_runtime(llm_kwargs: dict[str, Any]) -> Any:
    """Initialize and return the bedrock runtime client."""
    if "region_name" in llm_kwargs:
        return boto3.client("bedrock-runtime", region_name=llm_kwargs["region_name"])
    else:
        return boto3.client("bedrock-runtime")
