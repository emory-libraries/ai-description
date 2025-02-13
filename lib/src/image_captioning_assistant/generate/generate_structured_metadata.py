# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for an image."""

from typing import Any

from langchain_aws import ChatBedrockConverse
import boto3
import json

from image_captioning_assistant.data.data_classes import StructuredMetadata
from image_captioning_assistant.generate.utils import (
    format_prompt_for_claude,
    format_prompt_for_nova,
    encode_image_from_path,
    convert_bytes_to_base64_str,
    extract_json_and_cot_from_text,
)
import image_captioning_assistant.generate.prompts as p


def get_request_body(modelId, image_data, image_data_back=None):
    # Create the message with text and image
    messages_dict = {}
    messages_dict["claude"] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_data,
                    },
                },
                *[
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": idb,
                        },
                    } for idb in [image_data_back] if idb
                ],
                {"type": "text", "text": p.user_prompt},
            ],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": p.assistant_start}],
        },
    ]
    
    messages_dict["nova"] = [
        {
            "role": "user",
            "content": [
                {
                    # "type": "image",
                    "image": {"format": "jpeg", "source": {"bytes": image_data}}
                },
                {
                    # "type": "text",
                    "text": p.user_prompt
                },
            ],
        },
        {"role": "assistant", "content": [{"text": p.assistant_start}]},
    ]

    request_bodies = {}
    # Prepare the request bodies
    request_bodies["claude"] = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": p.system_prompt,
        "max_tokens": 4096,
        "temperature": 0.1,
        "top_p": 0.6,
        # "top_k": 250,
        # "stop_sequences": [''],
        "messages": messages_dict["claude"],
    }
    
    request_bodies["nova"] = {
        "schemaVersion": "messages-v1",
        "messages": messages_dict["nova"],
        "system": [{"text": p.system_prompt}],
        "toolConfig": {},
        "inferenceConfig": {
            "max_new_tokens": 4096,
            "top_p": 0.6,
            "top_k": 250,
            "temperature": 0.1,
            # ,"stopSequences": ['']
        },
    }

    return request_bodies[("claude" if 'claude' in modelId else "nova")]

def generate_structured_metadata(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    img_context: str,
    return_all=False, return_cot=False
) -> StructuredMetadata:
    """Generate structured metadata for an image.

    Args:
        img_bytes_list (list[bytes]): Image bytes - may include multiple (front and back) but at max two.  If two the latter is assumed to be the back
        llm_kwargs (dict[str, Any]): Keyword args for LLM
        img_context (str): Additional freeform context to help the LLM.

    Raises:
        ValueError: Error when model ID does not include nova or claude

    Returns:
        StructuredMetadata: Structured metadata for image.
    """
    
    # connect to runtime
    bedrock_runtime = boto3.client("bedrock-runtime")
    text_prompt = (
        p.user_prompt + 
        f"\nHere is some additional information that might help: {img_context}"
    )
    model_name = llm_kwargs.pop("model")
    if "nova" in model_name:
        prompt = format_prompt_for_nova(text_prompt, img_bytes_list)
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
        prompt = format_prompt_for_claude(text_prompt, img_bytes_list)
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
        response = bedrock_runtime.invoke_model(
            modelId=model_name, body=json.dumps(request_body)
        )
    
        # Process the response
        result = json.loads(response["body"].read())
        if 'claude' in model_name:
            llm_output = result["content"][0]["text"]
        elif 'nova' in model_name:
            llm_output = result["output"]["message"]["content"][0]["text"]
        else:
            raise ValueError("ModelId " + model_name + " not supported, must be set up")
        if return_all:
            return llm_output 
        else: # try to parse output
            try:
                cot, json_dict = extract_json_and_cot_from_text(llm_output)
                return (cot, StructuredMetadata(**json_dict)) if return_cot else StructuredMetadata(**json_dict)
            except Exception as e:
                print(e)
                print("trying again")


def extract_metadata_from_image(image_path, image_path_back=None
                                , return_all=False, return_cot=False
                                , modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"):
    # connect to runtime
    bedrock_runtime = boto3.client("bedrock-runtime")
    # Read and encode the image
    image_data = convert_bytes_to_base64_str(encode_image_from_path(image_path))
    if image_path_back:
        image_data_back = convert_bytes_to_base64_str(encode_image_from_path(image_path_back))
    else:
        image_data_back = None


    request_body = get_request_body(modelId, image_data, image_data_back)

    # Send the request to Bedrock and validate output.  Do in try-loop up to 5 times
    for _ in range(5):
        response = bedrock_runtime.invoke_model(
            modelId=modelId, body=json.dumps(request_body)
        )
    
        # Process the response
        result = json.loads(response["body"].read())
        if 'claude' in modelId:
            llm_output = result["content"][0]["text"]
        elif 'nova' in modelId:
            llm_output = result["output"]["message"]["content"][0]["text"]
        else:
            raise ValueError("ModelId " + modelId + " not supported, must be set up")
        if return_all:
            return llm_output 
        else: # try to parse output
            try:
                cot, json_dict = extract_json_and_cot_from_text(llm_output)
                return (cot, StructuredMetadata(**json_dict)) if return_cot else StructuredMetadata(**json_dict)
            except Exception as e:
                print(e)
                print("trying again")


