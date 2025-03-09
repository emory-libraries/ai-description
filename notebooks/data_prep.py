# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data prep utils for the api_gateway_demo notebook."""
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import boto3
import pandas as pd


def copy_s3_file(
    source_sha: str,
    dest_bucket: str,
    source_bucket: str = "fedora-cor-binaries",
    dest_folder: str = "images",
):
    """
    Copy a file from source bucket to destination bucket using get_object and put_object
    instead of copy_object to avoid permission issues.

    Args:
        source_sha (str): SHA1 hash of the source file
        source_bucket (str): Source S3 bucket name
        dest_bucket (str): Destination S3 bucket name
        dest_folder (str): Destination folder within the bucket

    Returns:
        bool: True if successful, False otherwise
    """
    s3_client = boto3.client("s3")

    source_path = source_sha
    dest_path = f"{dest_folder}/{source_sha}"

    try:
        logging.info(f"Copying {source_bucket}/{source_path} to {dest_bucket}/{dest_path}")

        # Method 1: Using memory buffer
        response = s3_client.get_object(Bucket=source_bucket, Key=source_path)
        file_content = response["Body"].read()

        s3_client.put_object(Body=file_content, Bucket=dest_bucket, Key=dest_path)
        return True
    except Exception as e:
        logging.error(f"Error copying {source_sha}: {str(e)}")

        # If the first method fails, try using the AWS CLI command directly
        try:
            logging.info(f"Trying alternative method with AWS CLI for {source_sha}")
            import subprocess

            cmd = f"aws s3 cp s3://{source_bucket}/{source_path} s3://{dest_bucket}/{dest_path}"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if process.returncode == 0:
                logging.info(f"Successfully copied {source_sha} using AWS CLI")
                return True
            else:
                logging.error(f"AWS CLI copy failed: {process.stderr}")
                return False
        except Exception as cli_error:
            logging.error(f"Error with AWS CLI method for {source_sha}: {str(cli_error)}")
            return False


def batch_copy_files_from_dataframe(df: pd.DataFrame, max_workers: int = 5) -> dict:
    """
    Process the dataframe and copy all page files to the destination bucket.

    Args:
        df (pandas.DataFrame): DataFrame with work_id, page_sha1, page_title columns
        max_workers (int): Maximum number of concurrent copy operations

    Returns:
        dict: Summary of copy operations with success and failure counts
    """
    # Extract all unique SHA1s from the dataframe
    all_sha1s = df["page_sha1"].unique().tolist()

    results = {"total": len(all_sha1s), "success": 0, "failure": 0, "failed_shas": []}

    logging.info(f"Starting copy of {len(all_sha1s)} files to the destination bucket")

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sha = {executor.submit(copy_s3_file, sha): sha for sha in all_sha1s}

        for future in future_to_sha:
            sha = future_to_sha[future]
            try:
                success = future.result()
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                    results["failed_shas"].append(sha)
            except Exception as e:
                logging.error(f"Exception for SHA {sha}: {str(e)}")
                results["failure"] += 1
                results["failed_shas"].append(sha)

    logging.info(f"Copy operation complete. Success: {results['success']}, Failures: {results['failure']}")

    return results


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


def create_metadata_job_objects(df: pd.DataFrame, bucket_name: str) -> list[dict]:
    """Create metadata job objects."""
    # Group by work_id
    grouped = df.groupby("work_id")

    result = []
    for work_id, group in grouped:
        # Create a dictionary to easily look up pages by title
        pages_dict = dict(zip(group["page_title"], group["page_sha1"]))

        # Order pages as Front -> Back
        page_shas = []
        if "Front" in pages_dict:
            page_shas.append(pages_dict["Front"])
        if "Back" in pages_dict:
            page_shas.append(pages_dict["Back"])

        # Create the object
        obj = {
            "work_id": work_id,
            "image_s3_uris": [f"s3://{bucket_name}/images/{sha}" for sha in page_shas],
        }
        result.append(obj)

    return result


def create_bias_job_objects(df: pd.DataFrame, bucket_name: str) -> list[dict]:
    """Create bias job objects."""
    # Group by work_id
    grouped = df.groupby("work_id")

    result = []
    for work_id, group in grouped:
        # Extract page numbers and sort them
        page_info = []
        for _, row in group.iterrows():
            page_title = row["page_title"]
            # Extract numeric part from page title (e.g., "Page 1" -> 1)
            try:
                page_num = int(page_title.split(" ")[1])
                page_info.append((page_num, row["page_sha1"]))
            except (IndexError, ValueError):
                # Handle cases where page_title doesn't follow "Page X" format
                page_info.append((999999, row["page_sha1"]))  # Put non-standard pages at the end

        # Sort by page number
        page_info.sort()

        # Get ordered page_shas
        page_shas = [sha for _, sha in page_info]

        # Get title and abstract (should be the same for all rows in group)
        title = group["title"].iloc[0]
        abstract = group["abstract"].iloc[0]

        # Create metadata dictionary
        metadata = {"title": title, "abstract": abstract}

        # Define the metadata S3 URI
        metadata_s3_uri = f"metadata/{work_id}.json"

        # Write metadata to S3
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=bucket_name,
            Key=f"metadata/{work_id}.json",
            Body=json.dumps(metadata),
            ContentType="application/json",
        )

        # Create the object
        obj = {
            "work_id": work_id,
            "image_s3_uris": [f"s3://{bucket_name}/images/{sha}" for sha in page_shas],
            "original_metadata_s3_uri": metadata_s3_uri,
        }
        result.append(obj)

    return result
