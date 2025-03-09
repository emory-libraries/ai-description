# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data prep utils for the api_gateway_demo notebook."""
import json
import logging
import os
import subprocess
import re

import boto3
import pandas as pd


def populate_bucket(bucket_name: str, image_fpath: str, context: str, metadata: str) -> tuple[str, str, str]:
    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Upload image file
    image_filename = os.path.basename(image_fpath)
    image_key = f"images/{image_filename}"
    s3_client.upload_file(image_fpath, bucket_name, image_key)
    # Create image S3 URI
    image_s3_uri = f"s3://{bucket_name}/{image_key}"
    # Upload metadata JSON file
    original_metadata_key = f"metadata/{os.path.splitext(image_filename)[0]}_metadata.txt"
    metadata_bytes = metadata.encode("utf-8")
    s3_client.put_object(Body=metadata_bytes, Bucket=bucket_name, Key=original_metadata_key)
    # Create metadata S3 URI
    original_metadata_s3_uri = f"s3://{bucket_name}/{original_metadata_key}"
    # Upload context JSON file
    context_key = f"contexts/{os.path.splitext(image_filename)[0]}_context.txt"
    context_bytes = context.encode("utf-8")
    s3_client.put_object(Body=context_bytes, Bucket=bucket_name, Key=context_key)
    # Create context S3 URI
    context_s3_uri = f"s3://{bucket_name}/{context_key}"

    return image_s3_uri, original_metadata_s3_uri, context_s3_uri


def copy_s3_file_using_subprocess(
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
) -> None:
    """Copy S3 file using subprocess"""
    logging.info(f"Trying alternative method with AWS CLI for {source_key}")

    cmd = f"aws s3 cp s3://{source_bucket}/{source_key} s3://{dest_bucket}/{dest_key}"
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if process.returncode == 0:
        logging.info(f"Successfully copied {source_key} using AWS CLI")
    else:
        logging.error(f"AWS CLI copy failed: {process.stderr}")


def copy_s3_file(
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
) -> None:
    """
    Copy a file from source bucket to destination bucket using get_object and put_object
    instead of copy_object to avoid permission issues.

    Args:
        source_bucket (str): Bucket of source file
        source_key (str): Key the source file
        dest_bucket (str): Bucket of destination file
        dest_key (str): Key of destination file
    """
    s3_client = boto3.client("s3")
    try:
        logging.info(f"Copying {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
        response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response["Body"].read()
        s3_client.put_object(Body=file_content, Bucket=dest_bucket, Key=dest_key)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        copy_s3_file_using_subprocess(
            source_bucket=source_bucket,
            source_key=source_key,
            dest_bucket=dest_bucket,
            dest_key=dest_key,
        )

def convert_page_to_index(page_string: str) -> int:
    # Handle "Front" case
    if page_string == "Front":
        return 0
    
    # Handle "Back" case
    elif page_string == "Back":
        return 1  # Or another appropriate value
    
    # Handle "Page X" case
    elif page_string.startswith("Page "):
        # Extract the number after "Page "
        match = re.search(r'Page (\d+)', page_string)
        if match:
            return int(match.group(1))
    raise ValueError("Page was not formatted as expected")


def prepare_images(
    work_df: pd.DataFrame,
    job_name: str,
    uploads_bucket: str,
    original_bucket: str,
) -> list[str]:
    """Copy images from original_bucket to uploads_bucket and return their folder URI.
    
    Images will be organized in uploads_bucket under job_name/work_id/images/
    """
    # Get work ID
    work_id = work_df['work_id'].iloc[0]
    # Create the destination path
    destination_folder = f"{job_name}/{work_id}/images/"    
    # Loop through each row in the dataframe
    for _, row in work_df.iterrows():
        # Get the original file path/key and other necessary info
        page_sha = row['page_sha1']
        page_index = convert_page_to_index(row["page_title"])
        # Copy the file with the new naming convention
        copy_s3_file(
            source_bucket=original_bucket,
            source_key=page_sha,
            dest_bucket=uploads_bucket,
            dest_key=f"{destination_folder}page_{page_index}_{page_sha}",
        )

    # Return the destination folder URI in S3 format
    return [f"s3://{uploads_bucket}/{destination_folder}"]


def prepare_metadata(
    work_df: pd.DataFrame,
    job_name: str,
    uploads_bucket: str,
) -> str:
    """Prepare metadata."""
    # Create metadata dictionary
    metadata = {
        "title": work_df["title"].iloc[0],
        "abstract": work_df["abstract"].iloc[0],
    }
    # Define the metadata S3 URI
    work_id = work_df["work_id"].iloc[0]
    metadata_s3_uri = f"{job_name}/{work_id}/metadata.json"
    # Write metadata to S3
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=uploads_bucket,
        Key=metadata_s3_uri,
        Body=json.dumps(metadata),
        ContentType="application/json",
    )
    # Create the object
    return metadata_s3_uri


def translate_csv_to_job_objects(
    csv_path: str,
    job_name: str,
    uploads_bucket: str,
    original_bucket: str = "fedora-cor-binaries"
) -> list[dict]:
    """Translate CSV into job objects."""
    # Load data
    df = pd.read_csv(csv_path)
    # Group by work_id
    grouped_df = df.groupby("work_id")

    job_objects = []
    for _, work_df in grouped_df:
        images_s3_uris = prepare_images(
            work_df=work_df,
            job_name=job_name,
            uploads_bucket=uploads_bucket,
            original_bucket=original_bucket,
        )
        metadata_s3_uri = prepare_metadata(
            work_df=work_df,
            uploads_bucket=uploads_bucket,
        )
        work_id = grouped_df["work_id"].iloc[0]
        job_object = {
            "work_id": work_id,
            "image_s3_uris": images_s3_uris,
            "original_metadata_s3_uri": metadata_s3_uri,
        }
        job_objects.append(job_object)
        
    return job_objects
