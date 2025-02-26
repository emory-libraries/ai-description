# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import base64
import json
from io import BytesIO
from typing import Any

from cloudpathlib import S3Path
from loguru import logger
from PIL import Image
from retry import retry

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.aws.s3 import load_to_bytes


def convert_bytes_to_base64_str(img_bytes: bytes) -> str:
    """Convert bytes to Base64 encoding.

    Args:
        img_bytes (bytes): Image bytes

    Returns:
        str: Image bytes as base64 string
    """
    return base64.b64encode(img_bytes).decode("utf-8")


def convert_and_reduce_image(image_bytes, max_dimension=2048, jpeg_quality=95):
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


def get_front_and_back_bytes_from_paths(image_path: str, image_path_back: str = None) -> tuple:
    """
    Encode the front image and optionally the back image of a ticket.

    Args:
        image_path (str): Path to the front image file.
        image_path_back (str, optional): Path to the back image file. Defaults to None.

    Returns:
        list: A list containing the base64 encoded strings of the front and back images (if provided).
    """
    image_list = []
    with open(image_path, "rb") as image_file:
        image_list.append(image_file.read())
    if image_path_back:
        with open(image_path_back, "rb") as image_file_back:
            image_list.append(image_file_back.read())
    return image_list


def encode_image_from_path(image_full_path, max_size=2048, jpeg_quality=95):
    with open(image_full_path, "rb") as image_file:
        # Open image and convert to RGB (removes alpha channel if present)
        image = Image.open(image_file).convert("RGB")

        # Set maximum dimensions while maintaining aspect ratio
        max_dimension = 2048  # Adjust this based on your size requirements
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        # Optimize JPEG quality and save to buffer
        buffer = BytesIO()
        image.save(
            buffer, format="JPEG", quality=jpeg_quality, optimize=True  # Adjust between 75-95 for quality/size balance
        )

        buffer.seek(0)
        image_data = buffer.read()

    return image_data


def extract_json_and_cot_from_text(text):
    # split chain of thought
    cot, text = text.split(p.COT_TAG_END)
    try:
        return (cot.replace(p.COT_TAG, ""), json.loads(text.strip()))
    except json.JSONDecodeError:
        print("Could not decode")
        print(text)
        raise json.JSONDecodeError


def format_prompt_for_claude(
    prompt: str, img_bytes_list: list[bytes], assistant_start: str | None = None
) -> list[dict]:
    """Format prompt for Anthropic Claude LLM.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Anthropic's Claude models.
    """
    content = [{"type": "text", "text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": convert_bytes_to_base64_str(img_bytes),
            },
        }
        content.append(img_message)
    msg_list = [{"role": "user", "content": content}]
    if assistant_start:
        msg_list.append({"role": "assistant", "content": assistant_start})
    return msg_list


def format_prompt_for_nova(prompt: str, img_bytes_list: list[bytes], assistant_start: str | None = None) -> list[dict]:
    """Format prompt for Amazon Nova models.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Amazon's Nova models.
    """
    content = [{"text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "image": {
                "format": "jpeg",
                "source": {"bytes": convert_bytes_to_base64_str(img_bytes)},
            }
        }
        content.append(img_message)
    msg_list = [{"role": "user", "content": content}]
    if assistant_start:
        msg_list.append({"role": "assistant", "content": assistant_start})
    return msg_list


def format_request_body(model_name: str, messages: list[dict]) -> dict:
    if "nova" in model_name:
        request_body = {
            "schemaVersion": "messages-v1",
            "messages": messages,
            "system": [{"text": p.system_prompt}],
            "toolConfig": {},
            "inferenceConfig": {
                "max_new_tokens": 4096,
                "top_p": 0.6,
                # "top_k": 250,
                "temperature": 0.1,
                # ,"stopSequences": ['']
            },
        }
    elif "claude" in model_name:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": p.system_prompt,
            "max_tokens": 4096,
            "temperature": 0.1,
            "top_p": 0.6,
            # "top_k": 250,
            # "stop_sequences": [''],
            "messages": messages,
        }
    else:
        raise ValueError(f"Expected 'nova' or 'claude' in model name, got {model_name}")
    return request_body


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
