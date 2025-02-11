"""Generate structured metadata for an image."""

from typing import Any

# from langchain_aws import ChatBedrockConverse
import boto3
import json

from image_captioning_assistant.data.data_classes import StructuredMetadata
from image_captioning_assistant.generate.utils import (
    format_prompt_for_claude,
    format_prompt_for_nova,
    convert_bytes_to_base64_str,
)
import image_captioning_assistant.generate.prompts as p


# def generate_structured_metadata(
#     img_bytes_list: list[bytes],
#     llm_kwargs: dict[str, Any],
#     img_context: str,
# ) -> StructuredMetadata:
#     """Generate structured metadata for an image.

#     Args:
#         img_bytes_list (list[bytes]): Image bytes - may include multiple (front and back)
#         llm_kwargs (dict[str, Any]): Keyword args for LLM
#         img_context (str): Additional freeform context to help the LLM.

#     Raises:
#         ValueError: Error when model ID does not include nova or claude

#     Returns:
#         StructuredMetadata: Structured metadata for image.
#     """
#     text_prompt = (
#         "Task: Review one or more images and generate structured metadata for it. "
#         f"Here is some additional information that might help: {img_context}"
#     )
#     model_name = llm_kwargs.pop("model")
#     if "nova" in model_name:
#         prompt = format_prompt_for_nova(text_prompt, img_bytes_list)
#     elif "claude" in model_name:
#         prompt = format_prompt_for_claude(text_prompt, img_bytes_list)
#     else:
#         raise ValueError(f"Expected 'nova' or 'claude' in model name, got {model_name}")
#     llm = ChatBedrockConverse(model=model_name, **llm_kwargs)
#     structured_llm = llm.with_structured_output(StructuredMetadata)
#     return structured_llm.invoke(prompt)

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
        "temperature": 0.0,
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
            "temperature": 0.0,
            # ,"stopSequences": ['']
        },
    }

    return request_bodies[("claude" if 'claude' in modelId else "nova")]

def extract_json_from_text(text):
    # remove chain of thought
    text = text.split(p.COT_TAG_END)[1].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("Could not decode")
        print(text)
        raise json.JSONDecodeError

def extract_metadata_from_image(image_path, image_path_back=None
                                , return_all=False
                                , modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"):
    # connect to runtime
    bedrock_runtime = boto3.client("bedrock-runtime")
    # Read and encode the image
    with open(image_path, "rb") as image_file:
        image_data = convert_bytes_to_base64_str(image_file.read())
    if image_path_back:
        with open(image_path_back, "rb") as image_file_back:
            image_data_back = convert_bytes_to_base64_str(image_file_back.read())
    else:
        image_data_back = None


    request_body = get_request_body(modelId, image_data, image_data_back)

    # Send the request to Bedrock
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
    return llm_output if return_all else extract_json_from_text(llm_output)



