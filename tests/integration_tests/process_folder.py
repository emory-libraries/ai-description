import argparse
from pathlib import Path
from typing import Any

from image_captioning_assistant.generate.generate_bias_analysis import (
    BiasAnalysis,
    generate_bias_analysis,
)


def process_folder(
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
        dict[str, BiasAnalysis]: Bias analysis for each image.
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
                print(f"Error processing {file_path}: {str(e)}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a folder of images.")
    parser.add_argument(
        "--folder_path",
        type=str,
        required=True,
        help="Local path to the folder containing images",
    )
    args = parser.parse_args()
    process_folder(folder_path=Path(args.folder_path), llm_kwargs={"model": ""})
