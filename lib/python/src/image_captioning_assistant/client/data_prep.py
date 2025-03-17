# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data prep utils for the api_gateway_demo notebook."""
import concurrent.futures
import json
import logging
import os
import re
import subprocess
import tempfile
from functools import partial
from io import BytesIO

import boto3
import pandas as pd
from PIL import Image
from tqdm import tqdm


def populate_bucket(
    bucket_name: str,
    image_fpath: str,
    context: str,
    metadata: str,
    convert_jpeg: bool = True,
) -> tuple[str, str, str]:
    """
    Upload image and related files to S3 bucket, with option to convert image to JPEG.

    Args:
        bucket_name (str): Target S3 bucket
        image_fpath (str): Path to local image file
        context (str): Context text
        metadata (str): Metadata text
        convert_jpeg (bool): Whether to convert the image to JPEG

    Returns:
        tuple[str, str, str]: URIs for image, metadata, and context
    """
    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Get image filename and create key
    image_filename = os.path.basename(image_fpath)
    base_name = os.path.splitext(image_filename)[0]

    if convert_jpeg:
        # Convert the image to JPEG
        try:
            img = Image.open(image_fpath)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Save to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
                img.save(temp_path, format="JPEG", quality=95)

            # Use the temporary file for upload
            image_key = f"images/{base_name}.jpg"
            s3_client.upload_file(temp_path, bucket_name, image_key, ExtraArgs={"ContentType": "image/jpeg"})

            # Clean up
            os.unlink(temp_path)
        except Exception as e:
            logging.error(f"Failed to convert image: {str(e)}. Uploading original.")
            image_key = f"images/{image_filename}"
            s3_client.upload_file(image_fpath, bucket_name, image_key)
    else:
        # Upload original image file
        image_key = f"images/{image_filename}"
        s3_client.upload_file(image_fpath, bucket_name, image_key)

    # Create image S3 URI
    image_s3_uri = f"s3://{bucket_name}/{image_key}"

    # Upload metadata JSON file
    original_metadata_key = f"metadata/{base_name}_metadata.txt"
    metadata_bytes = metadata.encode("utf-8")
    s3_client.put_object(Body=metadata_bytes, Bucket=bucket_name, Key=original_metadata_key)
    # Create metadata S3 URI
    original_metadata_s3_uri = f"s3://{bucket_name}/{original_metadata_key}"

    # Upload context JSON file
    context_key = f"contexts/{base_name}_context.txt"
    context_bytes = context.encode("utf-8")
    s3_client.put_object(Body=context_bytes, Bucket=bucket_name, Key=context_key)
    # Create context S3 URI
    context_s3_uri = f"s3://{bucket_name}/{context_key}"

    return image_s3_uri, original_metadata_s3_uri, context_s3_uri


def convert_to_jpeg(file_content: bytes) -> bytes:
    """
    Convert binary image data to JPEG format

    Args:
        file_content (bytes): Binary image data

    Returns:
        bytes: JPEG formatted image data
    """
    try:
        # Open the image with PIL
        img = Image.open(BytesIO(file_content))

        # Convert to RGB if needed (in case of RGBA or other formats)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Save as JPEG to a BytesIO object
        output = BytesIO()
        img.save(output, format="JPEG", quality=95)

        # Get the bytes
        jpeg_content = output.getvalue()
        return jpeg_content
    except Exception as e:
        logging.error(f"Failed to convert image to JPEG: {str(e)}")
        # Return original content if conversion fails
        return file_content


def copy_s3_file_using_subprocess(
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
    convert_jpeg: bool = True,
) -> None:
    """Copy S3 file using subprocess"""
    logging.debug(f"Trying alternative method with AWS CLI for {source_key}")

    if convert_jpeg:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name

        # Download the file
        download_cmd = f"aws s3 cp s3://{source_bucket}/{source_key} {temp_path}"
        subprocess.run(download_cmd, shell=True, check=True)

        # Convert to JPEG
        try:
            img = Image.open(temp_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(temp_path, format="JPEG", quality=95)
        except Exception as e:
            logging.error(f"Failed to convert image using subprocess method: {str(e)}")

        # Upload the converted file
        upload_cmd = f"aws s3 cp {temp_path} s3://{dest_bucket}/{dest_key}"
        process = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)

        # Clean up
        os.unlink(temp_path)
    else:
        cmd = f"aws s3 cp s3://{source_bucket}/{source_key} s3://{dest_bucket}/{dest_key}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if process.returncode == 0:
        logging.debug(f"Successfully copied {source_key} using AWS CLI")
    else:
        logging.error(f"AWS CLI copy failed: {process.stderr}")


def copy_s3_file(
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
    convert_jpeg: bool = True,
) -> None:
    """
    Copy a file from source bucket to destination bucket, optionally converting to JPEG.

    Args:
        source_bucket (str): Bucket of source file
        source_key (str): Key the source file
        dest_bucket (str): Bucket of destination file
        dest_key (str): Key of destination file
        convert_jpeg (bool): Whether to convert the file to JPEG
    """
    s3_client = boto3.client("s3")
    try:
        logging.debug(f"Copying {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
        response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
        file_content = response["Body"].read()

        # Convert to JPEG if requested
        if convert_jpeg:
            file_content = convert_to_jpeg(file_content)

        s3_client.put_object(Body=file_content, Bucket=dest_bucket, Key=dest_key, ContentType="image/jpeg")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        copy_s3_file_using_subprocess(
            source_bucket=source_bucket,
            source_key=source_key,
            dest_bucket=dest_bucket,
            dest_key=dest_key,
            convert_jpeg=convert_jpeg,
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
        match = re.search(r"Page (\d+)", page_string)
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
    work_id = work_df["work_id"].iloc[0]
    # Create the destination path
    destination_folder = f"{job_name}/{work_id}/images/"
    # Loop through each row in the dataframe

    for _, row in tqdm(work_df.iterrows(), total=len(work_df)):
        # Get the original file path/key and other necessary info
        page_sha = row["page_sha1"]
        page_index = convert_page_to_index(row["page_title"])
        # Copy the file with the new naming convention and convert to JPEG
        copy_s3_file(
            source_bucket=original_bucket,
            source_key=page_sha,
            dest_bucket=uploads_bucket,
            dest_key=f"{destination_folder}page_{page_index:05d}_{page_sha}.jpg",
            convert_jpeg=True,
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
    metadata_s3_key = f"{job_name}/{work_id}/metadata.json"
    # Write metadata to S3
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=uploads_bucket,
        Key=metadata_s3_key,
        Body=json.dumps(metadata),
        ContentType="application/json",
    )
    # Create the URI
    return f"s3://{uploads_bucket}/{metadata_s3_key}"


def translate_csv_to_job_objects(
    csv_path: str,
    job_name: str,
    uploads_bucket: str,
    original_bucket: str = "fedora-cor-binaries",
    max_workers: int = 10,
) -> list[dict]:
    """Translate CSV into job objects with parallel processing."""
    # Load data
    df = pd.read_csv(csv_path)
    # Group by work_id
    grouped_df = df.groupby("work_id")

    # Process each work_id group in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a partial function with common parameters
        process_work_group = partial(
            process_single_work_group, job_name=job_name, uploads_bucket=uploads_bucket, original_bucket=original_bucket
        )

        # Submit all work groups for processing
        future_to_work_id = {
            executor.submit(process_work_group, work_id, group_df): work_id for work_id, group_df in grouped_df
        }

        # Collect results as they complete
        job_objects = []
        for future in concurrent.futures.as_completed(future_to_work_id):
            job_objects.append(future.result())

    return job_objects


def process_single_work_group(work_id, work_df, job_name, uploads_bucket, original_bucket):
    """Process a single work group to create a job object."""
    images_s3_uris = prepare_images_parallel(
        work_df=work_df,
        job_name=job_name,
        uploads_bucket=uploads_bucket,
        original_bucket=original_bucket,
    )
    metadata_s3_uri = prepare_metadata(
        work_df=work_df,
        job_name=job_name,
        uploads_bucket=uploads_bucket,
    )

    return {
        "work_id": work_id,
        "image_s3_uris": images_s3_uris,
        "original_metadata_s3_uri": metadata_s3_uri,
    }


def prepare_images_parallel(work_df, job_name, uploads_bucket, original_bucket, max_workers=5):
    """Copy images in parallel using ThreadPoolExecutor."""
    work_id = work_df["work_id"].iloc[0]
    destination_folder = f"{job_name}/{work_id}/images/"

    # Create a list of tasks (rows to process)
    tasks = []
    for _, row in work_df.iterrows():
        page_sha = row["page_sha1"]
        page_index = convert_page_to_index(row["page_title"])
        dest_key = f"{destination_folder}page_{page_index:05d}_{page_sha}.jpg"
        tasks.append((original_bucket, page_sha, uploads_bucket, dest_key))

    # Process images in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(
            tqdm(
                executor.map(lambda args: copy_s3_file(*args, True), tasks),
                total=len(tasks),
                desc=f"Processing images for work_id {work_id}",
            )
        )

    return [f"s3://{uploads_bucket}/{destination_folder}"]
