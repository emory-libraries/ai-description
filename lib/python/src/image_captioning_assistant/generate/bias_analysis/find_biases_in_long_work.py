# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

import logging
from typing import Any

import boto3

from image_captioning_assistant.data.data_classes import Bias, Biases, BiasLevel, BiasType, WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.find_biases_in_short_work import find_biases_in_short_work

logger = logging.getLogger(__name__)


def create_error_bias() -> Biases:
    """Create fill-in object for when individual page cannot be processed."""
    return Biases(biases=[Bias(level=BiasLevel.high, type=BiasType.other, explanation="COULD NOT PROCESS PAGE")])


def find_biases_in_original_metadata(
    original_metadata: str,
    bedrock_runtime: Any,
    llm_kwargs: dict,
    work_context: str | None = None,
) -> Biases:
    """Find biases in original metadata."""
    logger.info("Analyzing original metadata")
    llm_output = find_biases_in_short_work(
        image_s3_uris=[],  # no images
        s3_kwargs={},  # no need for s3
        llm_kwargs=llm_kwargs,
        resize_kwargs={},  # no need for resize
        work_context=work_context,
        original_metadata=original_metadata,
        bedrock_runtime=bedrock_runtime,
    )
    # return only metadata biases
    return llm_output.metadata_biases


def find_biases_in_images(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    bedrock_runtime: Any,
    llm_kwargs: dict,
    work_context: str | None = None,
) -> list[Biases]:
    """Find biases in an image."""
    logger.info(f"Analyzing {len(image_s3_uris)} images")
    page_biases = []
    for image_s3_uri in image_s3_uris:
        logger.debug(f"Analyzing image {image_s3_uri}")
        try:
            llm_output = find_biases_in_short_work(
                image_s3_uris=[image_s3_uri],  # one image
                s3_kwargs=s3_kwargs,
                llm_kwargs=llm_kwargs,
                resize_kwargs=resize_kwargs,
                work_context=work_context,
                bedrock_runtime=bedrock_runtime,
            )
            page_biases.append(llm_output.page_biases[0])
        except Exception as exc:
            logger.warning(f"Failed to process {image_s3_uri}: {exc}")
            biases_error = create_error_bias()
            page_biases.append(biases_error)

    return page_biases


def find_biases_in_long_work(
    image_s3_uris: list[str],
    s3_kwargs: dict[str, Any],
    llm_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    original_metadata: str | None = None,
    work_context: str | None = None,
) -> WorkBiasAnalysis:
    """Find image and metadata biases independently."""
    if "region_name" in llm_kwargs:
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=llm_kwargs["region_name"])
    else:
        bedrock_runtime = boto3.client("bedrock-runtime")
    metadata_biases: Biases = Biases(biases=[])
    if original_metadata:
        metadata_biases.biases = find_biases_in_original_metadata(
            original_metadata=original_metadata,
            work_context=work_context,
            bedrock_runtime=bedrock_runtime,
            llm_kwargs=llm_kwargs,
        )

    page_biases: list[Biases] = find_biases_in_images(
        image_s3_uris=image_s3_uris,
        bedrock_runtime=bedrock_runtime,
        llm_kwargs=llm_kwargs,
        resize_kwargs=resize_kwargs,
        s3_kwargs=s3_kwargs,
        work_context=work_context,
    )
    try:
        return WorkBiasAnalysis(
            metadata_biases=metadata_biases,
            page_biases=page_biases,
        )
    except Exception as e:
        logger.warning("Failed to cast metadata biases and page biases into WorkBiasAnalysis, debug to log full output")
        logger.debug(f"metadata_biases:\n {str(metadata_biases)} \n\n\n")
        logger.debug(f"page_biases:\n {str(page_biases)} \n\n\n")
        raise e
