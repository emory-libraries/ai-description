# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from enum import Enum

import pandas as pd

from image_captioning_assistant.aws.s3 import copy_s3_object


class Columns(Enum):
    """Columns in ground_truth.csv"""

    file_set_id = "file_set_id"
    work_link = "work_link"
    file_set_link = "file_set_link"
    collection_link = "collection_link"
    notes_from_elizabeth = "notes_from_elizabeth"
    page_context_from_elizabeth = "page_context_from_elizabeth"
    category_from_elizabeth = "category_from_elizabeth"
    title = "title"
    abstract = "abstract"
    administrative_unit = "administrative_unit"
    contact_information = "contact_information"
    content_genres = "content_genres"
    content_type = "content_type"
    date_created = "date_created"
    deduplication_key = "deduplication_key"
    emory_rights_statements = "emory_rights_statements"
    extent = "extent"
    holding_repository = "holding_repository"
    institution = "institution"
    legacy_rights = "legacy_rights"
    local_call_number = "local_call_number"
    notes = "notes"
    other_identifiers = "other_identifiers"
    rights_statement = "rights_statement"
    subject_geo = "subject_geo"
    subject_names = "subject_names"
    subject_topics = "subject_topics"
    sublocation = "sublocation"
    page_sha1 = "page_sha1"
    page_title = "page_title"


def get_image_keys(csv_path: str) -> list[str]:
    """Get image keys referenced by ground_truth.csv."""
    df = pd.read_csv(csv_path)
    return df[Columns.page_sha1].to_list()


def copy_over_annotated_images(
    csv_path: str,
    output_bucket: str,
    output_prefix: str,
    input_bucket: str = "fedora-cor-binaries",
) -> None:
    """Copy over images referenced by ground_truth.csv to a sandbox bucket."""
    for image_key in get_image_keys(csv_path=csv_path):
        copy_s3_object(
            source_bucket=input_bucket,
            source_key=image_key,
            dest_bucket=output_bucket,
            dest_key=f"{output_prefix}/{image_key}",
        )
