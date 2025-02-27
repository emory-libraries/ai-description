# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for a work."""

import json
import logging
from typing import Any

import boto3
from cloudpathlib import S3Path
from pydantic_core import ValidationError

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.aws.s3 import load_to_str
from image_captioning_assistant.data.data_classes import Metadata
from image_captioning_assistant.generate.utils import (
    extract_json_and_cot_from_text,
    format_prompt_for_claude,
    format_prompt_for_nova,
    format_request_body,
    LLMResponseParsingError,
    load_and_resize_images,
)

logger = logging.getLogger(__name__)


def generate_structured_metadata(
    img_bytes_list: list[bytes], llm_kwargs: dict[str, Any], work_context: str | None = None
) -> Metadata:
    """Generate structured metadata for an image using foundation models.

    Args:
        img_bytes_list: List of image bytes (front/back images, max 2 items)
        llm_kwargs: LLM configuration parameters including:
            - model: Model ID (must contain 'nova' or 'claude')
            - region_name: (Optional) AWS region override
        work_context: Additional context to assist metadata generation

    Returns:
        Dictionary containing:
        - cot: Chain of Thought reasoning text
        - metadata: Structured metadata object

    Raises:
        ValueError: For unsupported model types
        RuntimeError: After 5 failed attempts to parse model output
    """
    # Configure Bedrock client
    if "region_name" in llm_kwargs:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=llm_kwargs["region_name"])
    else:
        bedrock_runtime = boto3.client("bedrock-runtime")
    # Construct augmented prompt
    text_prompt = f"{p.user_prompt_metadata}\nContextual Help: {work_context}"
    model_name: str = llm_kwargs["model_id"]
    court_order = False
    # Create messages
    if "claude" in model_name:
        messages = format_prompt_for_claude(
            prompt=text_prompt,
            img_bytes_list=img_bytes_list,
            assistant_start=p.COT_TAG,
        )
    elif "nova" in model_name:
        messages = format_prompt_for_nova(
            prompt=text_prompt,
            img_bytes_list=img_bytes_list,
            assistant_start=p.COT_TAG,
        )
    else:
        raise ValueError(f"model {model_name} not supported")

    # Retry loop for robustness around structured metadata
    for attempt in range(5):
        try:
            request_body = format_request_body(model_name, messages, court_order=court_order)
            response = bedrock_runtime.invoke_model(modelId=model_name, body=json.dumps(request_body))

            # Process the response
            result = json.loads(response["body"].read())
            if "claude" in model_name:
                llm_output = result["content"][0]["text"]
            elif "nova" in model_name:
                llm_output = result["output"]["message"]["content"][0]["text"]
            else:
                raise ValueError("ModelId " + model_name + " not supported, must be set up")

            cot, json_dict = extract_json_and_cot_from_text(llm_output)
            logger.info(f"\n\n********** CHAIN OF THOUGHT **********\n {cot} \n\n")
            return Metadata(**json_dict["metadata"])

        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/5 failed: {str(e)}")
            if attempt == 4:
                # need to raise exception that was thrown for debugging purposes as invocation is in try block
                raise e

            if isinstance(e, LLMResponseParsingError) or isinstance(e, ValidationError):
                raw_output = llm_output.split(p.COT_TAG_END)[-1]
                logger.debug("Raw model output:", raw_output)
                if (
                    "apologize" in raw_output.lower()
                    or "i cannot" in raw_output.lower()
                    or "i can't" in raw_output.lower()
                ):
                    court_order = True

    raise RuntimeError("Failed to parse model output after 5 attempts")


def generate_work_structured_metadata(
    image_s3_uris: str,
    llm_kwargs: dict[str, Any],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    context_s3_uri: str | None = None,
) -> Metadata:
    """Generate structured metadata for a work."""
    # Enforce max length of two
    if len(image_s3_uris) > 2:
        msg = f"Structured metadata only supports documents of 1-2 pages, {len(image_s3_uris)} pages provided."
        logger.warning(msg)
        raise ValueError(msg)
    # Establish a default model
    if "model_id" not in llm_kwargs:
        llm_kwargs["model_id"] = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
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
    # Invoke function
    return generate_structured_metadata(
        img_bytes_list=img_bytes_list,
        llm_kwargs=llm_kwargs,
        work_context=work_context,
    )
