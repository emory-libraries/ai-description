# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import json
from typing import Any

import boto3
import image_captioning_assistant.generate.prompts as p
from image_captioning_assistant.data.data_classes import StructuredMetadata
from image_captioning_assistant.generate.utils import (
    convert_and_reduce_image,
    extract_json_and_cot_from_text,
    format_prompt_for_claude,
    format_prompt_for_nova,
)


def generate_bias_analysis(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> StructuredMetadata:
    """Generate bias analysis for an image.

    Args:
        img_bytes_list (list[bytes]): Image bytes - may include multiple (front and back)
        llm_kwargs (dict[str, Any]): Keyword args for LLM
        img_context (str): Additional freeform context to help the LLM.

    Raises:
        ValueError: Error when model ID does not include nova or claude

    Returns:
        BiasAnalysis: Structured bias analysis for image.
    """
    # connect to runtime
    if "region_name" in llm_kwargs:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=llm_kwargs.pop("region_name"))
    else:
        bedrock_runtime = boto3.client("bedrock-runtime")

        # convert and resize image bytes if necessary
    img_bytes_list_resize = [
        convert_and_reduce_image(image_bytes, max_dimension=2048, jpeg_quality=95) for image_bytes in img_bytes_list
    ]

    text_prompt = p.user_prompt_bias_only + f"\nHere is some additional information that might help: {img_context}"
    model_name = llm_kwargs.pop("model")
    if "nova" in model_name:
        prompt = format_prompt_for_nova(text_prompt, img_bytes_list_resize)
        request_body = {
            "schemaVersion": "messages-v1",
            "messages": prompt,
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
        prompt = format_prompt_for_claude(text_prompt, img_bytes_list_resize)
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": p.system_prompt,
            "max_tokens": 4096,
            "temperature": 0.1,
            "top_p": 0.6,
            # "top_k": 250,
            # "stop_sequences": [''],
            "messages": prompt,
        }
    else:
        raise ValueError(f"Expected 'nova' or 'claude' in model name, got {model_name}")
    # Send the request to Bedrock and validate output.  Do in try-loop up to 5 times
    for _ in range(5):
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
            return StructuredMetadata(cot=cot, **json_dict)
        except Exception as e:
            # TODO: add detailed logging of llm_output somewhere
            print(e)
            print(llm_output.split(p.COT_TAG_END)[1])
            print("trying again")
