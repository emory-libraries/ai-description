# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import os
import sys

from csv_mock_db_manager import CSVMockDatabaseManager
from dotenv import load_dotenv
from image_captioning_assistant.orchestrate.process_job import process_job
from loguru import logger

logger.remove()
logger.add(sink=sys.stderr, level="INFO")

load_dotenv()

# Load environment variables
batch_job_name = os.environ["BATCH_JOB_NAME"]
s3_bucket = os.environ["S3_BUCKET"]
s3_prefix = os.environ["S3_PREFIX"]
aws_region = os.environ["AWS_REGION"]
skip_completed = os.environ.get("SKIP_COMPLETED", "False").lower() == "true"

# Create a CSV mock DatabaseManager
csv_db_manager = CSVMockDatabaseManager()

# Run the process_job function with CSV mock database
try:
    process_job(
        batch_job_name=batch_job_name,
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        db_manager=csv_db_manager,
        aws_region=aws_region,
        skip_completed=skip_completed,
    )
    logger.info("Job processing completed successfully.")

    # Write the results to CSV files
    csv_db_manager.write_to_csv()
    logger.info("Results written to CSV files.")
except Exception as e:
    logger.warning(f"An error occurred during job processing: {str(e)}")
    raise e

# Print out some information about the mock calls
logger.info("\nDatabase interactions:")
for table_name, rows in csv_db_manager.data.items():
    logger.info(f"{table_name}: {len(rows)} rows")
