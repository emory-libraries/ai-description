"""Generate bias analysis for an image."""

from pathlib import Path
from typing import Any

from langchain_aws import ChatBedrockConverse
from loguru import logger
from tqdm import tqdm

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


def generate_bias_analysis_for_folder(
    folder_path: Path,
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> dict[str, BiasAnalysis]:
    """Process folder.

    Args:
        folder_path (Path): Path to folder of images.
        llm_kwargs (dict[str, Any]): Keyword args for LLM.
        img_context (str): Additional context for interpreting the images.

    Returns:
        dict[str, BiasAnalysis]: Bias analysis for each file.
    """
    results = {}
    # Iterate through files in the folder
    for file_path in folder_path.iterdir():
        # Check if the file is an image (based on extension)
        if file_path.is_file() and file_path.suffix.lower() in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
        ]:
            try:
                # Load the image bytes
                with open(file_path, "rb") as img_file:
                    img_bytes = img_file.read()

                img_bytes_list = [img_bytes]

                # Analyze the image
                bias_analysis = generate_bias_analysis(
                    img_bytes_list=img_bytes_list,
                    llm_kwargs=llm_kwargs,
                    img_context=img_context,
                )

                # Store the result
                results[str(file_path)] = bias_analysis

            except Exception as e:
                logger.exception(f"Error processing {file_path}: {str(e)}")

    return results
