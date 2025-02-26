# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

from pathlib import Path
from typing import Any

from cloudpathlib import S3Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from retry import retry

from image_captioning_assistant.aws.s3 import load_to_bytes
from image_captioning_assistant.generate.utils import (
    convert_and_reduce_image,
    format_prompt_for_claude,
    format_prompt_for_nova,
)

COT_TAG_NAME = "object_detail_and_bias_analysis"
COT_TAG = f"<{COT_TAG_NAME}>"
COT_TAG_END = f"</{COT_TAG_NAME}>"

jinja_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "prompts"), autoescape=True)


def create_messages(
    img_bytes_list: list[bytes],
    work_context: str | None = None,
    original_metadata: str | None = None,
    model_name: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
) -> dict[str, Any]:
    """Create Messages list to pass to LLM, supports Claude and Nova models"""
    # Create system prompt
    prompt_template = jinja_env.get_template("user_prompt_bias.jinja")
    inputs = {
        "work_context": work_context,
        "original_metadata": original_metadata,
        "COT_TAG_NAME": COT_TAG_NAME,
        "COT_TAG": COT_TAG,
        "COT_TAG_END": COT_TAG_END,
    }
    prompt = prompt_template.render(inputs)
    logger.debug(f"PROMPT:\n```\n{prompt}\n```\n")
    # Create messages
    if "claude" in model_name:
        messages = format_prompt_for_claude(
            prompt=prompt,
            img_bytes_list=img_bytes_list,
        )
    elif "nova" in model_name:
        messages = format_prompt_for_nova(
            prompt=prompt,
            img_bytes_list=img_bytes_list,
        )
    else:
        raise ValueError(f"model {model_name} not supported")
    return messages


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
    logger.info("Invoking structured LLM...")
    response = structured_llm.invoke(messages)
    logger.info("Invocation successful")
    return response
