# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import logging
from typing import Any

from image_captioning_assistant.data.data_classes import WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.utils import (
    call_model,
    create_messages,
    parse_model_output,
    prepare_images,
)
from image_captioning_assistant.generate.utils import initialize_bedrock_runtime, needs_court_order

logger = logging.getLogger(__name__)


def find_biases_in_short_work(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    llm_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],  # default max_dimension=2048, jpeg_quality=95
    work_context: str | None = None,
    original_metadata: str | None = None,
    bedrock_runtime: Any | None = None,
) -> WorkBiasAnalysis:
    """Find biases in one or two images and, optionally, their existing metadata."""
    model_name = llm_kwargs["model_id"]

    # Initialize bedrock runtime if not provided
    if bedrock_runtime is None:
        bedrock_runtime = initialize_bedrock_runtime(llm_kwargs)

    # Load and resize images
    img_bytes_list = prepare_images(image_s3_uris, s3_kwargs, resize_kwargs, model_name)

    # Create messages
    messages = create_messages(
        img_bytes_list=img_bytes_list,
        work_context=work_context,
        original_metadata=original_metadata,
        model_name=model_name,
    )

    court_order = False
    llm_output = ""

    # Retry loop for robustness around structured metadata
    for attempt in range(5):
        try:
            # Call the model
            llm_output = call_model(bedrock_runtime, model_name, messages, court_order)

            # Parse output and validate
            cot, work_bias_analysis = parse_model_output(llm_output, len(image_s3_uris))

            # Log chain of thought
            logger.info(f"\n\n********** CHAIN OF THOUGHT **********\n {cot} \n\n")

            return work_bias_analysis

        except Exception as e:
            logger.warning(f"Attempt {attempt+1}/5 failed: {str(e)}")
            if attempt == 4:
                # need to raise exception that was thrown for debugging purposes
                raise e

            # Check if we need to use court order prompt
            if needs_court_order(e, llm_output):
                court_order = True

    raise RuntimeError("Failed to parse model output after 5 attempts")
