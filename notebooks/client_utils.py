# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Client utils for the api_gateway_demo notebook."""
import json
import logging

import requests


def submit_job(
    api_url: str,
    job_name: str,
    job_type: str,
    works: list,
    api_key: str,
) -> dict:
    """Submit job."""
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/create_job"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    request_body = {"job_name": job_name, "job_type": job_type, "works": works}

    # Make the POST request
    response = requests.post(endpoint, data=json.dumps(request_body), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        return response.json()
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_job_progress(api_url: str, job_name: str, api_key: str) -> dict:
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
    headers = {"x-api-key": api_key}

    # Make the GET request
    response = requests.get(endpoint, params=params, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        return response.json()
    # Check if the item was not found
    if response.status_code == 404:
        # Parse the JSON response
        logging.error(f"Error: API request failed with status code {response.status_code}")
        return response.json()
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_overall_progress(api_url: str, api_key: str) -> dict:
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
    headers = {"x-api-key": api_key}

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        return response.json()
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def get_job_results(api_url: str, job_name: str, work_id: str, api_key: str) -> dict:
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
    headers = {"x-api-key": api_key}

    # Make the GET request
    response = requests.get(endpoint, params=params, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        return response.json()
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()


def update_job_results(api_url: str, job_name: str, work_id: str, api_key: str) -> dict:
    # Construct the full URL
    api_url = api_url.rstrip("/")
    endpoint = f"{api_url}/results"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    updated_fields = {"work_status": "REVIEWED"}
    request_body = {"job_name": job_name, "work_id": work_id, "updated_fields": updated_fields}

    # Make the POST request
    response = requests.post(endpoint, data=json.dumps(request_body), headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        return response.json()
    else:
        logging.error(f"Error: API request failed with status code {response.status_code}")
        logging.error(f"Response: {response.text}")
        response.raise_for_status()
