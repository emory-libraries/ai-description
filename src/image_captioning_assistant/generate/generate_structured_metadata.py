"""Generate structured metadata for an image."""

from typing import Any
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from loguru import logger

from image_captioning_assistant.data.data_classes import StructuredMetadata
from image_captioning_assistant.generate.utils import (
    format_prompt_for_claude,
    format_prompt_for_nova,
)


def generate_structured_metadata(
    img_bytes_list: list[bytes],
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> StructuredMetadata:
    """Generate structured metadata for an image.

    Args:
        img_bytes_list (list[bytes]): Image bytes - may include multiple (front and back)
        llm_kwargs (dict[str, Any]): Keyword args for LLM
        img_context (str): Additional freeform context to help the LLM.

    Raises:
        ValueError: Error when model ID does not include nova or claude

    Returns:
        StructuredMetadata: Structured metadata for image.
    """
    text_prompt = (
        "Task: Review one or more images and generate structured metadata for it. "
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
    structured_llm = llm.with_structured_output(StructuredMetadata)
    return structured_llm.invoke(prompt)


def generate_structured_metadata_for_folder(
    folder_path: Path,
    llm_kwargs: dict[str, Any],
    img_context: str,
) -> dict[str, StructuredMetadata]:
    """Process folder.

    Args:
        folder_path (Path): Path to folder of images.
        llm_kwargs (dict[str, Any]): Keyword args for LLM.
        img_context (str): Additional context for interpreting the images.

    Returns:
        dict[str, StructuredMetadata]: Structured metadata for each file.
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
                structured_metadata = generate_structured_metadata(
                    img_bytes_list=img_bytes_list,
                    llm_kwargs=llm_kwargs,
                    img_context=img_context,
                )

                # Store the result
                results[str(file_path)] = structured_metadata

            except Exception as e:
                logger.exception(f"Error processing {file_path}: {str(e)}")

    return results
