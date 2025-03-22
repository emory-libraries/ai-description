# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import logging
from typing import Any

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.data.data_classes import WorkBiasAnalysis
from image_captioning_assistant.generate.errors import LLMResponseParsingError
from image_captioning_assistant.generate.utils import (
    extract_json_and_cot_from_text,
    format_prompt_for_converse,
    load_and_resize_images,
)

logger = logging.getLogger(__name__)


def prepare_images(
    image_s3_uris: list[str], s3_kwargs: dict[str, Any], resize_kwargs: dict[str, Any], model_name: str
) -> list[bytes]:
    """Load and resize images from S3 URIs."""
    if len(image_s3_uris) > 2:
        raise RuntimeError("maximum of 2 images (front and back) supported for short work")

    if len(image_s3_uris) == 0:
        return []

    # Adjust resize parameters for specific models
    if "llama" in model_name:
        resize_kwargs["max_dimension"] = 1024

    return load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)


def call_model(bedrock_runtime: Any, model_name: str, messages: list[dict[str, Any]], court_order: bool = False) -> str:
    """Call the model and return the output."""
    sys_prompt = p.system_prompt_court_order if court_order else p.system_prompt

    response = bedrock_runtime.converse(
        modelId=model_name,
        messages=messages,
        system=[{"text": sys_prompt}],
        inferenceConfig={
            "temperature": 0.1,
            "maxTokens": 4000,
            "topP": 0.6,
        },
    )

    # Log token usage from the response
    input_tokens = response["usage"]["inputTokens"]
    output_tokens = response["usage"]["outputTokens"]

    logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")

    return response["output"]["message"]["content"][0]["text"]


def parse_model_output(llm_output: str, image_count: int) -> tuple[str, WorkBiasAnalysis]:
    """Parse the model output and validate the result."""
    cot, json_dict = extract_json_and_cot_from_text(llm_output)

    # validate correct number of biases output
    if image_count > 0 and image_count != len(json_dict["page_biases"]):
        raise LLMResponseParsingError(f"incorrect number of bias lists for {image_count} pages")

    return cot, WorkBiasAnalysis(**json_dict)


def create_messages(
    img_bytes_list: list[bytes],
    work_context: str | None = None,
    original_metadata: str | None = None,
    model_name: str = "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
) -> dict[str, Any]:
    """Create Messages list to pass to LLM, supports Claude and Nova models"""
    # Create system prompt
    prompt = p.bias_analysis_template.render(
        COT_TAG=p.COT_TAG,
        COT_TAG_END=p.COT_TAG_END,
        COT_TAG_NAME=p.COT_TAG_NAME,
        work_context=work_context,
        original_metadata=original_metadata,
    )
    logger.debug(f"PROMPT:\n```\n{prompt}\n```\n")
    messages = format_prompt_for_converse(
        prompt=prompt,
        img_bytes_list=img_bytes_list,
        assistant_start=(p.COT_TAG if "llama" not in model_name else None),
    )
    return messages
