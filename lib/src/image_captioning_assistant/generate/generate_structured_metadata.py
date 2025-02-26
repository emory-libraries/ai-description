# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for a work."""

import json
import logging
from typing import Any

import boto3
from cloudpathlib import S3Path

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.aws.s3 import load_to_str
from image_captioning_assistant.data.data_classes import Metadata, MetadataCOT
from image_captioning_assistant.generate.utils import (
    extract_json_and_cot_from_text,
    format_prompt_for_claude,
    format_prompt_for_nova,
    LLMResponseParsingError,
    load_and_resize_images,
)

logger = logging.getLogger(__name__)


class DocumentLengthError(Exception):
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"DocumentLengthError: {self.message} (Error Code: {self.error_code})"


def generate_structured_metadata(
    img_bytes_list: list[bytes], llm_kwargs: dict[str, Any], work_context: str | None = None
) -> MetadataCOT:
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
    system_prompt = p.system_prompt
    assistant_start = p.assistant_start
    # Configure model-specific parameters
    if "nova" in model_name:
        request_body = {
            "schemaVersion": "messages-v1",
            "system": [{"text": system_prompt}],
            "toolConfig": {},
            "inferenceConfig": {"max_new_tokens": 4096, "top_p": 0.6, "temperature": 0.1},
            "messages": format_prompt_for_nova(
                prompt=text_prompt,
                img_bytes_list=img_bytes_list,
                assistant_start=assistant_start,
            ),
        }
    elif "claude" in model_name:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": system_prompt,
            "max_tokens": 4096,
            "temperature": 0.1,
            "top_p": 0.6,
            "stop_sequences": ["<innerthinking.md>"],
            "messages": format_prompt_for_claude(
                prompt=text_prompt,
                img_bytes_list=img_bytes_list,
                assistant_start=assistant_start,
            ),
        }
    else:
        raise ValueError(f"Unsupported model: {model_name}. Requires 'nova' or 'claude'")
    # Retry loop for robustness around structured metadata
    for attempt in range(5):
        try:
            response = bedrock_runtime.invoke_model(modelId=model_name, body=json.dumps(request_body))
            result = json.loads(response["body"].read())

            # Model-specific response parsing
            if "claude" in model_name:
                llm_output = result["content"][0]["text"]
            else:  # Nova
                llm_output = result["output"]["message"]["content"][0]["text"]

            cot, json_dict = extract_json_and_cot_from_text(llm_output)
            return MetadataCOT(cot=cot, **json_dict["metadata"])

        except Exception as e:
            logger.debug(f"Attempt {attempt+1}/5 failed: {str(e)}")

            if isinstance(e, LLMResponseParsingError):
                raw_output = llm_output.split(p.COT_TAG_END)[-1]
                logger.debug("Raw model output:", raw_output)
                if (
                    "apologize" in raw_output.lower()
                    or "i cannot" in raw_output.lower()
                    or "i can't" in raw_output.lower()
                ):
                    system_prompt = p.system_prompt_court_order
                    assistant_start = p.assistant_start_court_order

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
        raise DocumentLengthError(msg)
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
