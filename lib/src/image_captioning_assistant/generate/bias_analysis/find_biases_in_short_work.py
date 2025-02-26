# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import json
from typing import Any

import boto3
from loguru import logger

from image_captioning_assistant.data.data_classes import WorkBiasAnalysisCOT
from image_captioning_assistant.generate.bias_analysis.utils import (
    create_messages,
    load_and_resize_images,
)
from image_captioning_assistant.generate.utils import extract_json_and_cot_from_text, format_request_body


def find_biases_in_short_work(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    llm_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    work_context: str | None = None,
    original_metadata: str | None = None,
) -> WorkBiasAnalysisCOT:
    """Find biases in one or two images and, optionally, their existing metadata."""
    #     # connect to runtime
    if "region_name" in llm_kwargs:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=llm_kwargs.pop("region_name"))
    else:
        bedrock_runtime = boto3.client("bedrock-runtime")
    # Load and resize image bytes
    img_bytes_list = load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)
    # Create messages and request body
    model_name = llm_kwargs.pop("model_id")
    messages = create_messages(
        img_bytes_list=img_bytes_list,
        work_context=work_context,
        original_metadata=original_metadata,
        model_name=model_name,
    )
    request_body = format_request_body(model_name, messages)
    for attempt in range(5):
        response = bedrock_runtime.invoke_model(modelId=model_name, body=json.dumps(request_body))

        # Process the response
        result = json.loads(response["body"].read())
        if "claude" in model_name:
            llm_output = result["content"][0]["text"]
        elif "nova" in model_name:
            llm_output = result["output"]["message"]["content"][0]["text"]
        else:
            raise ValueError("ModelId " + model_name + " not supported, must be set up")
        # Try parsing output and if structured output fails to hold, try again up to 5x
        try:
            cot, json_dict = extract_json_and_cot_from_text(llm_output)
            assert len(image_s3_uris) == len(
                json_dict["page_biases"]
            ), f"incorrect number of bias lists for {len(image_s3_uris)} pages"
            return WorkBiasAnalysisCOT(cot=cot, **json_dict)
        except Exception as e:
            # TODO: add detailed logging of llm_output somewhere
            logger.warning(f"Exception:\n{str(e)}\n")
            logger.debug(f"Model Output:\n```\n{llm_output}\n```\n")
            logger.warning(f"trying again, retry number {attempt+1}")
    
    raise RuntimeError("Unable to generate response, enable debug and check log")
