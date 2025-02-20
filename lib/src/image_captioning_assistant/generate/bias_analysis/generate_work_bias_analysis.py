# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Generate bias analysis for an image."""

from typing import Any

from cloudpathlib import S3Path

from image_captioning_assistant.aws.s3 import load_to_str
from image_captioning_assistant.data.data_classes import WorkBiasAnalysis
from image_captioning_assistant.generate.bias_analysis.find_biases_in_long_work import find_biases_in_long_work
from image_captioning_assistant.generate.bias_analysis.find_biases_in_short_work import find_biases_in_short_work


def generate_work_bias_analysis(
    image_s3_uris: str,
    llm_kwargs: dict[str, Any],
    s3_kwargs: dict[str, Any],
    resize_kwargs: dict[str, Any],
    context_s3_uri: str | None = None,
    original_metadata_s3_uri: str | None = None,
) -> WorkBiasAnalysis:
    """Find biases across an arbitrarily long work."""
    original_metadata = None
    # If metadata was provided
    if original_metadata_s3_uri:
        # Retrieve it from S3
        s3_path = S3Path(context_s3_uri)
        original_metadata = load_to_str(
            s3_bucket=s3_path.bucket,
            s3_key=s3_path.key,
            s3_client_kwargs=s3_kwargs,
        )

    work_context = None
    # If context was provided
    if context_s3_uri:
        # Retrieve it from S3
        s3_path = S3Path(context_s3_uri)
        work_context = load_to_str(
            s3_bucket=s3_path.bucket,
            s3_key=s3_path.key,
            s3_client_kwargs=s3_kwargs,
        )

    # If it's a short document, analyze metadata (if available) and image(s) all together
    if len(image_s3_uris) <= 2:
        return find_biases_in_short_work(
            image_s3_uris=image_s3_uris,
            s3_kwargs=s3_kwargs,
            resize_kwargs=resize_kwargs,
            llm_kwargs=llm_kwargs,
            work_context=work_context,
            original_metadata=original_metadata,
        )

    # Otherwise analyze metadata (if available) and then each image independently
    else:
        return find_biases_in_long_work(
            image_s3_uris=image_s3_uris,
            llm_kwargs=llm_kwargs,
            s3_kwargs=s3_kwargs,
            original_metadata=original_metadata,
            work_context=work_context,
            resize_kwargs=resize_kwargs,
        )
