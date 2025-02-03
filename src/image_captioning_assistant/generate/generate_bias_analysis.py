"""Generate bias analysis for an image."""

from typing import Any

from langchain_aws import ChatBedrockConverse

from image_captioning_assistant.data.data_classes import BiasAnalysis
from image_captioning_assistant.generate.utils import (
    format_prompt_for_claude,
    format_prompt_for_nova,
)


def generate_bias_analysis(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> BiasAnalysis:
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
    text_prompt = (
        "Task: Review one or more images and analyze any bias in it. "
        f"Here is some additional information that might help: {img_context}"
    )
    model_name = llm_kwargs.pop("model")
    if "nova" in model_name:
        prompt = format_prompt_for_nova(text_prompt, img_bytes_list)
    elif "claude" in model_name:
        prompt = format_prompt_for_claude(text_prompt, img_bytes_list)
    else:
        raise ValueError(f"Expected 'nova' or 'claude' in model name, got {model_name}")
    llm = ChatBedrockConverse(model=model_name, **llm_kwargs)
    structured_llm = llm.with_structured_output(BiasAnalysis)
    return structured_llm.invoke(prompt)
