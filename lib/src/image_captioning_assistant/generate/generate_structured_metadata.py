# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate structured metadata for an image using foundation models."""

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


def generate_structured_metadata(
    img_bytes_list: list[bytes], llm_kwargs: dict[str, Any], img_context: str
) -> StructuredMetadata:
    """Generate structured metadata for an image using foundation models.

    Args:
        img_bytes_list: List of image bytes (front/back images, max 2 items)
        llm_kwargs: LLM configuration parameters including:
            - model: Model ID (must contain 'nova' or 'claude')
            - region_name: (Optional) AWS region override
        img_context: Additional context to assist metadata generation

    Returns:
        Dictionary containing:
        - cot: Chain of Thought reasoning text
        - metadata: Structured metadata object

    Raises:
        ValueError: For unsupported model types
        RuntimeError: After 5 failed attempts to parse model output
    """
    # Resize and optimize images for model consumption
    img_bytes_list_resize = [
        convert_and_reduce_image(image_bytes, max_dimension=2048, jpeg_quality=95) for image_bytes in img_bytes_list
    ]

    # Configure Bedrock client
    region = llm_kwargs.pop("region_name", None)
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=region) if region else boto3.client("bedrock-runtime")

    # Construct augmented prompt
    text_prompt = f"{p.user_prompt}\nContextual Help: {img_context}"
    model_name: str = llm_kwargs.pop("model")

    # Configure model-specific parameters
    if "nova" in model_name:
        request_body = {
            "schemaVersion": "messages-v1",
            "system": [{"text": p.system_prompt}],
            "toolConfig": {},
            "inferenceConfig": {"max_new_tokens": 4096, "top_p": 0.6, "temperature": 0.1, **llm_kwargs},
            "messages": format_prompt_for_nova(text_prompt, img_bytes_list_resize),
        }
    elif "claude" in model_name:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": p.system_prompt,
            "max_tokens": 4096,
            "temperature": 0.1,
            "top_p": 0.6,
            **llm_kwargs,
            "messages": format_prompt_for_claude(text_prompt, img_bytes_list_resize),
        }
    else:
        raise ValueError(f"Unsupported model: {model_name}. Requires 'nova' or 'claude'")

    # Retry loop for robustness
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
            return StructuredMetadata(cot=cot, **json_dict)

        except Exception as e:
            if attempt == 4:
                raise RuntimeError("Failed to parse model output after 5 attempts") from e
            print(f"Attempt {attempt+1}/5 failed: {str(e)}")
            print("Raw model output:", llm_output.split(p.COT_TAG_END)[-1])

    raise RuntimeError("Unexpected error in retry loop")
