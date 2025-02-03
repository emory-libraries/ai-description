from typing import Any
import base64

from langchain_aws import ChatBedrockConverse

from image_captioning_assistant.data.data_classes import StructuredMetadata


def convert_bytes_to_base64_str(img_bytes: bytes) -> str:
    """Convert bytes to Base64 encoding.

    Args:
        img_bytes (bytes): Image bytes

    Returns:
        str: Image bytes as base64 string
    """
    return base64.b64encode(img_bytes).decode("utf-8")


def format_prompt_for_claude(prompt: str, img_bytes_list: list[bytes]) -> list[dict]:
    """Format prompt for Anthropic Claude LLM.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Anthropic's Claude models.
    """
    content = [{"type": "text", "text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": convert_bytes_to_base64_str(img_bytes),
            },
        }
        content.append(img_message)
    return [{"role": "user", "content": content}]


def format_prompt_for_nova(prompt: str, img_bytes_list: list[bytes]) -> list[dict]:
    """Format prompt for Amazon Nova models.

    Args:
        prompt (str): Text prompt for model
        img_bytes_list (list[bytes]): Image(s) for model

    Returns:
        list[dict]: Prompt formatted for Amazon's Nova models.
    """
    content = [{"text": prompt}]
    for img_bytes in img_bytes_list:
        img_message = {
            "image": {
                "format": "jpeg",
                "source": {"bytes": convert_bytes_to_base64_str(img_bytes)},
            }
        }
        content.append(img_message)
    return [{"role": "user", "content": content}]


def generate_structured_metadata(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> StructuredMetadata:
    text_prompt = (
        "Task: Review one or more images and generate structured metadata for it. "
        f"Here is some historical context that might help: {img_context}"
    )
    model_name = llm_kwargs.pop("model")
    if "nova" in model_name:
        prompt = format_prompt_for_nova(text_prompt, img_bytes_list)
    elif "claude" in model_name:
        prompt = format_prompt_for_claude(text_prompt, img_bytes_list)
    else:
        raise ValueError(f"Expected 'nova' or 'claude' in model name, got {model_name}")
    llm = ChatBedrockConverse(model=model_name, **llm_kwargs)
    structured_llm = llm.with_structured_output(StructuredMetadata)
    return structured_llm.invoke(prompt)
