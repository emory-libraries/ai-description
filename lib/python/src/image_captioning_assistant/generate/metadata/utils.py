# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Helper functions for generating structured metadata."""

import logging
from typing import Any

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.data.data_classes import Metadata
from image_captioning_assistant.generate.utils import extract_json_and_cot_from_text, format_prompt_for_converse

logger = logging.getLogger(__name__)


def prepare_model_invocation(
    model_name: str, img_bytes_list: list[bytes], work_context: str | None, court_order: bool = False
) -> tuple[Any, list]:
    """Prepare the model invocation parameters.

    Args:
        model_name: Model ID to use
        img_bytes_list: List of image bytes
        work_context: Additional context to assist metadata generation
        court_order: Whether to use court order prompt

    Returns:
        tuple: Prepared parameters for model invocation
    """
    # Construct prompt
    text_prompt = f"{p.user_prompt_metadata}\nContextual Help: {work_context}"

    # Format messages for API
    messages = format_prompt_for_converse(
        prompt=text_prompt,
        img_bytes_list=img_bytes_list,
        assistant_start=(p.COT_TAG if "llama" not in model_name else None),
    )

    # Create system instructions
    sys_prompt = p.system_prompt_court_order if court_order else p.system_prompt

    return {
        "modelId": model_name,
        "messages": messages,
        "system": [{"text": sys_prompt}],
        "inferenceConfig": {
            "temperature": 0.1,
            "maxTokens": 4000,
            "topP": 0.6,
        },
    }


def invoke_model_and_process_response(bedrock_runtime: Any, invoke_params: dict) -> Metadata:
    """Invoke the model and process its response.

    Args:
        bedrock_runtime: Bedrock runtime client
        invoke_params: Parameters for model invocation

    Returns:
        Metadata: Structured metadata object

    Raises:
        LLMResponseParsingError: If JSON parsing fails
        ValidationError: If schema validation fails
    """
    # Invoke the model
    response = bedrock_runtime.converse(**invoke_params)
    llm_output = response["output"]["message"]["content"][0]["text"]

    # Parse output and extract metadata
    cot, json_dict = extract_json_and_cot_from_text(llm_output)
    logger.info(f"\n\n********** CHAIN OF THOUGHT **********\n {cot} \n\n")

    # Validate and return structured metadata
    return Metadata(**json_dict)
