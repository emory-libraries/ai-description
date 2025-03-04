# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Utils for the api_gateway_demo notebook."""
import json
import logging
import os

import boto3
import requests


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
        "desription": "offensive image",
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


def log_in(api_url: str, username: str, password: str):
    """Authenticate identity."""
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
        return data
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        return response


def create_dummy_job(
    api_url: str,
    job_name: str,
    job_type: str,
    original_metadata_s3_uri: str,
    context_s3_uri: str,
    image_s3_uri: str,
):
    """Create dummy job."""
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/create_job"

    # Headers
    headers = {"Content-Type": "application/json"}

    works = [
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


def get_job_progress(api_url: str, job_name: str):
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

    # Make the GET request
    response = requests.get(endpoint, params=params)

    # Check the status code
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        logging.info(f"No data found for job_name: {job_name}")
        return response.json()
    else:
        response.raise_for_status()


def get_overall_progress(api_url: str):
    """Query the overall_progress endpoint

    Args:
    api_url (str): The base URL of your API Gateway

    Returns:
    dict: The JSON response from the API, or None if an error occurred
    """
    api_url = api_url.rstrip("/")
    # Construct the full URL
    endpoint = f"{api_url}/overall_progress"

    # Make the GET request
    response = requests.get(endpoint)

    # Check the status code
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_job_results(api_url: str, job_name: str, work_id: str):
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

    # Make the GET request
    response = requests.get(endpoint, params=params)

    # Check the status code
    if response.status_code == 200:
        return response.json()["item"]
    elif response.status_code == 404:
        msg = f"No data found for job_name={job_name} and work_id={work_id}"
        logging.error(f"No data found for job_name={job_name} and work_id={work_id}")
        raise Exception(msg)
    else:
        response.raise_for_status()


def update_job_results(api_url: str, job_name: str, work_id: str):
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/results"

    # Headers
    headers = {"Content-Type": "application/json"}

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
