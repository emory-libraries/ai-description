import os

import pandas as pd
from dotenv import load_dotenv

from client_utils import submit_job
from data_prep import translate_csv_to_job_objects

load_dotenv()

api_key = os.environ["API_KEY"]
api_url = "https://g1k4qurjll.execute-api.us-east-1.amazonaws.com/dev/api"
uploads_bucket = "ai-description-dev-nt01-008971633436-uploads"

# Process bias test set
job_name="bias_test_set"
bias_uri = "s3://gaiic-emory-dev/bias_test_set.csv"
bias_objects = translate_csv_to_job_objects(
    csv_path=bias_uri,
    job_name=job_name,
    uploads_bucket=uploads_bucket,
    original_bucket="fedora-cor-binaries"
)
submit_job(
    api_url=api_url,
    job_name=job_name,
    job_type="bias",
    works=bias_objects,
    api_key=api_key,
)

# Process metadata test set
job_name = "metadata_test_set"
metadata_uri = "s3://gaiic-emory-dev/metadata_test_set.csv"
metadata_objects = translate_csv_to_job_objects(
    csv_path=metadata_uri,
    job_name=job_name,
    uploads_bucket=uploads_bucket,
    original_bucket="fedora-cor-binaries"
)
submit_job(
    api_url=api_url,
    job_name=job_name,
    job_type="metadata",
    works=bias_objects,
    api_key=api_key,
)
