"""ECS worker script."""

import contextlib
import json
import logging
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Generator

import boto3
import pandas as pd
from botocore.config import Config
from botocore.exceptions import ClientError
from tqdm import tqdm

tqdm.pandas()

# Constants
AWS_REGION = os.environ["AWS_REGION"]
S3_BUCKET = os.environ["S3_BUCKET"]
S3_CONFIG = Config(
    {
        "s3": {"addressing_style": "virtual"},
        "signature_version": "s3v4",
    }
)
RESULTS_BUCKET = os.environ["RESULTS_BUCKET"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
JOB_ID = os.environ["JOB_ID"]

# Initialize AWS clients globally
s3 = boto3.client("s3", config=S3_CONFIG, region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
ses = boto3.client("ses", region_name=AWS_REGION)

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def download_file(bucket: str, key: str, download_path: Path) -> None:
    """Download file from S3.

    Args:
        bucket (str): Bucket where file will be downloaded from.
        key (str): Key where file will be downloaded from.
        download_path (Path): Path where file will be downloaded to.
    """
    try:
        s3.download_file(bucket, key, download_path)
        logger.info(f"Downloaded {key} from S3 bucket {bucket}")
    except ClientError as e:
        logger.error(f"Failed to download file from S3: {str(e)}")
        raise


def upload_file(file_path: Path, bucket: str, key: str) -> None:
    """Upload file to S3.

    Args:
        file_path (Path): Path to local file.
        bucket (str): Bucket where file will be written.
        key (str): Key where file will be written.
    """
    try:
        s3.upload_file(file_path, bucket, key)
        logger.info(f"Uploaded results to S3 bucket {bucket} with key {key}")
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {str(e)}")
        raise


@contextlib.contextmanager
def error_handler(step_name: str, job_id: str) -> Any:
    """Handle potential error.

    Args:
        step_name (str): Name of step in process.
        job_id (str): ID of job.
    """
    try:
        yield
    except Exception as e:
        logger.error(f"Error in {step_name} for job {job_id}: {str(e)}")
        try:
            # Update DynamoDB with failed status
            table = dynamodb.Table(DYNAMODB_TABLE)
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "FAILED"},
            )
        except Exception as update_error:
            logger.error(f"Failed to update job status to FAILED: {update_error}")
        raise  # Re-raise the original exception


@contextlib.contextmanager
def extracted_zip(zip_path: Path) -> Generator[Path | None, None, None]:
    """Extract a zip file to a temporary directory.

    Args:
        zip_path (Path): Path to zip file.

    Yields:
        Generator[Path | None, None, None]: Paths to individual files in zip.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmp_dir)
            yield Path(tmp_dir)
        except Exception as e:
            logger.exception(f"An error occurred while extracting {zip_path}: {str(e)}")
            yield None


def read_json_zip(download_path: Path) -> pd.DataFrame:
    """Read a zipped zipfile with jsons and reads them into a single pandas DF.

    Args:
        download_path (Path): Path where zip will be read from.

    Returns:
        pd.DataFrame: Table containing contents of zip file.
    """
    with extracted_zip(download_path) as tmp_path:
        if tmp_path:
            try:
                # Load dataframe
                return pd.DataFrame()

            except Exception as e:
                logger.error(f"Unexpected error processing files: {str(e)}")
                return pd.DataFrame()
        else:
            logger.error("Failed to create temporary directory for the unzipped content")
            return pd.DataFrame()


def process_job(
    job_id: str,
    s3_bucket: str,
    results_bucket: str,
    dynamodb_table: str,
) -> None:
    """Process job.

    Args:
        job_id (str): ID of the job - in practice this is a filename.
        s3_bucket (str): Bucket where input file is stored.
        results_bucket (str): Bucket where output file will be stored.
        dynamodb_table (str): DynamoDB table where job status is tracked.
    """
    # Use a dedicated data directory in the container
    data_dir = Path("/app/data")
    data_dir.mkdir(parents=True, exist_ok=True)

    basename = Path(job_id).stem
    download_path = data_dir / job_id
    results_filename = f"{basename}-result.csv"
    result_path = data_dir / results_filename

    try:
        # Download file for processing
        with error_handler("file download", job_id):
            download_file(
                bucket=s3_bucket,
                key=job_id,
                download_path=download_path,
            )

        # Process the file
        with error_handler("file processing", job_id):
            # Process new CSV
            logger.info("Loading zip file")
            input_df = read_json_zip(download_path)
            logger.info("Processing items in zip file")
            # PROCESS HERE
            results = None
            # Write to local temp file
            logger.debug("Writing results temporarily to CSV")
            results.to_csv(result_path, index=False)

        # Upload result to S3
        with error_handler("result upload", job_id):
            upload_file(
                file_path=result_path,
                bucket=results_bucket,
                key=results_filename,
            )

        # Update DynamoDB with status and S3 path
        with error_handler("status update", job_id):
            table = dynamodb.Table(dynamodb_table)
            table.update_item(
                Key={"job_id": job_id},
                UpdateExpression="SET #s = :s, #p = :p",
                ExpressionAttributeNames={"#s": "status", "#p": "result_path"},
                ExpressionAttributeValues={":s": "COMPLETED", ":p": f"s3://{results_bucket}/{results_filename}"},
            )
            logger.info("Updated job status and result path in DynamoDB")

    finally:
        # Clean up files
        logger.info("Cleaning up files")
        download_path.unlink(missing_ok=True)
        result_path.unlink(missing_ok=True)


def main() -> None:
    """Main function executed by ECS job."""
    try:
        process_job(
            job_id=JOB_ID,
            s3_bucket=S3_BUCKET,
            results_bucket=RESULTS_BUCKET,
            dynamodb_table=DYNAMODB_TABLE,
        )
    except Exception:
        # Any unhandled exceptions will be caught here
        logger.error(f"Job {JOB_ID} failed to complete")
        sys.exit(1)


if __name__ == "__main__":
    main()
