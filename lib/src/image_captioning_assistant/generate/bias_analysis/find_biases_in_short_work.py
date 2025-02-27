# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import json
import logging
from typing import Any

import boto3
from pydantic_core import ValidationError

import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.data.data_classes import WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.utils import create_messages, load_and_resize_images
from image_captioning_assistant.generate.utils import (
    extract_json_and_cot_from_text,
    format_request_body,
    LLMResponseParsingError,
)

logger = logging.getLogger(__name__)


def find_biases_in_short_work(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    llm_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    work_context: str | None = None,
    original_metadata: str | None = None,
    bedrock_runtime: Any | None = None,
) -> WorkBiasAnalysis:
    """Find biases in one or two images and, optionally, their existing metadata."""
    #     # connect to runtime if not provided
    if bedrock_runtime is None:
        if "region_name" in llm_kwargs:
            bedrock_runtime = boto3.client("bedrock-runtime", region_name=llm_kwargs["region_name"])
        else:
            bedrock_runtime = boto3.client("bedrock-runtime")
    # Load and resize image bytes
    if len(image_s3_uris) > 2:
        return RuntimeError("maximum of 2 images (front and back) supported for short work")
    if len(image_s3_uris) > 0:
        img_bytes_list = load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)
    else:
        img_bytes_list = []
    # Create messages and request body
    model_name = llm_kwargs["model_id"]
    messages = create_messages(
        img_bytes_list=img_bytes_list,
        work_context=work_context,
        original_metadata=original_metadata,
        model_name=model_name,
    )
    court_order = False
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

            # parse output and log chain of thought
            cot, json_dict = extract_json_and_cot_from_text(llm_output)
            logger.info(f"\n\n********** CHAIN OF THOUGHT **********\n {cot} \n\n")
            # validate correct number of biases output
            if len(image_s3_uris) != len(json_dict["page_biases"]):
                raise LLMResponseParsingError(f"incorrect number of bias lists for {len(image_s3_uris)} pages")
            return WorkBiasAnalysis(**json_dict)

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
