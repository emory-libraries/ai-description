# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Utils for the api_gateway_demo notebook."""
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
import pandas as pd
import requests


def copy_s3_file(
    source_sha,
    source_bucket="fedora-cor-binaries",
    dest_bucket="ai-description-dev-nt01-008971633436-uploads",
    dest_folder="images",
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


def batch_copy_files_from_dataframe(df, max_workers=5):
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


def populate_bucket(bucket_name: str, image_fpath: str) -> tuple[str, str, str]:
    # Initialize S3 client
    s3_client = boto3.client("s3")

    # Upload image file
    image_filename = os.path.basename(image_fpath)
    image_key = f"images/{image_filename}"
    s3_client.upload_file(image_fpath, bucket_name, image_key)
    # Create image S3 URI
    image_s3_uri = f"s3://{bucket_name}/{image_key}"

    # Create metadata
    original_metadata = {
        "title": "foo",
        "description": "offensive image",
    }
    # Convert metadata to JSON
    original_metadata_json = json.dumps(original_metadata)
    # Upload metadata JSON file
    original_metadata_key = f"metadata/{os.path.splitext(image_filename)[0]}_metadata.json"
    s3_client.put_object(Body=original_metadata_json, Bucket=bucket_name, Key=original_metadata_key)
    # Create metadata S3 URI
    original_metadata_s3_uri = f"s3://{bucket_name}/{original_metadata_key}"

    # Convert context data to JSON
    context_str = "This document is old"
    # Upload context JSON file
    context_key = f"contexts/{os.path.splitext(image_filename)[0]}_context.txt"
    s3_client.put_object(Body=context_str, Bucket=bucket_name, Key=context_key)
    # Create context S3 URI
    context_s3_uri = f"s3://{bucket_name}/{context_key}"

    return image_s3_uri, original_metadata_s3_uri, context_s3_uri


def get_session_token(api_url: str, username: str, password: str) -> str:
    """Get JWT."""
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/log_in"

    # Headers
    headers = {"Content-Type": "application/json"}

    request_body = {"username": username, "password": password}

    # Make the POST request
    response = requests.post(endpoint, data=json.dumps(request_body), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
        return data["sessionToken"]
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


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


def create_dummy_job_objects(
    job_name: str,
    job_type: str,
    original_metadata_s3_uri: str,
    context_s3_uri: str,
    image_s3_uri: str,
    session_token: str,
):
    """Create dummy job."""
    return [
        {
            "work_id": f"{job_name}_short_work",
            "image_s3_uris": [image_s3_uri],
            "context_s3_uri": context_s3_uri,
            "original_metadata_s3_uri": original_metadata_s3_uri,
        },
        {
            "work_id": f"{job_name}_long_work",
            "image_s3_uris": [image_s3_uri, image_s3_uri, image_s3_uri, image_s3_uri],
            "context_s3_uri": context_s3_uri,
            "original_metadata_s3_uri": original_metadata_s3_uri,
        },
    ]


def submit_job(
    api_url: str,
    job_name: str,
    job_type: str,
    works: list,
    session_token: str,
):
    """Submit job."""
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/create_job"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_token}",
        "X-Request-Timestamp": str(int(time.time() * 1000)),  # Milliseconds since epoch
    }
    request_body = {"job_name": job_name, "job_type": job_type, "works": works}

    # Make the POST request
    response = requests.post(endpoint, data=json.dumps(request_body), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_job_progress(api_url: str, job_name: str, session_token: str) -> dict:
    """Query the job_progress endpoint with the given job_name.

    Args:
    api_url (str): The base URL of your API Gateway
    job_name (str): The name of the job to query

    Returns:
    dict: The JSON response from the API, or None if an error occurred
    """
    api_url = api_url.rstrip("/")
    # Construct the full URL
    endpoint = f"{api_url}/job_progress"

    # Set up the query parameters
    params = {"job_name": job_name}

    # Headers
    headers = {
        "Authorization": f"Bearer {session_token}",
        "X-Request-Timestamp": str(int(time.time() * 1000)),  # Milliseconds since epoch
    }

    # Make the GET request
    response = requests.get(endpoint, params=params, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
        return data
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_overall_progress(api_url: str, session_token: str) -> dict:
    """Query the overall_progress endpoint

    Args:
    api_url (str): The base URL of your API Gateway

    Returns:
    dict: The JSON response from the API, or None if an error occurred
    """
    api_url = api_url.rstrip("/")
    # Construct the full URL
    endpoint = f"{api_url}/overall_progress"

    # Headers
    headers = {
        "Authorization": f"Bearer {session_token}",
        "X-Request-Timestamp": str(int(time.time() * 1000)),  # Milliseconds since epoch
    }

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
        return data
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_job_results(api_url: str, job_name: str, work_id: str, session_token: str) -> dict:
    """
    Query the results endpoint with the given job_name and work_id.

    Args:
    api_url (str): The base URL of your API Gateway.
    job_name (str): The name of the job to query.
    work_id (str): The ID of the work within the job.

    Returns:
    dict: The JSON response from the API, or None if an error occurred
    """
    api_url = api_url.rstrip("/")
    # Construct the full URL
    endpoint = f"{api_url}/results"

    # Set up the query parameters
    params = {"job_name": job_name, "work_id": work_id}

    # Headers
    headers = {
        "Authorization": f"Bearer {session_token}",
        "X-Request-Timestamp": str(int(time.time() * 1000)),  # Milliseconds since epoch
    }

    # Make the GET request
    response = requests.get(endpoint, params=params, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
        return data
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def update_job_results(api_url: str, job_name: str, work_id: str, session_token: str) -> None:
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/results"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_token}",
        "X-Request-Timestamp": str(int(time.time() * 1000)),  # Milliseconds since epoch
    }

    updated_fields = {"work_status": "REVIEWED"}
    request_body = {"job_name": job_name, "work_id": work_id, "updated_fields": updated_fields}

    # Make the POST request
    response = requests.post(endpoint, data=json.dumps(request_body), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        logging.info(f"API Response: {data}")
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()
