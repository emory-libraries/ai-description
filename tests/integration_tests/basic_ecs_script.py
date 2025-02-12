# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""ECS worker script."""

import logging
import os
import sys

from image_captioning_assistant.data.db.config import Config as DbConfig
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.tables.batch_job import update_batch_job
from image_captioning_assistant.orchestrate.process_job import process_job

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


if __name__ == "__main__":
    batch_job_name = os.environ.get("BATCH_JOB_NAME", "BATCH JOB NAME NOT PROVIDED")
    try:
        db_manager = DatabaseManager(
            DbConfig(
                db_name=os.environ["DB_NAME"],
                db_port=os.environ["DB_PORT"],
                db_reader_host=os.environ["DB_READER_HOST"],
                db_writer_host=os.environ["DB_WRITER_HOST"],
            )
        )
        process_job(
            batch_job_name=batch_job_name,
            s3_bucket=os.environ["S3_BUCKET"],
            s3_prefix=os.environ["S3_PREFIX"],
            aws_region=os.environ["AWS_REGION"],
        )
        job_status = "COMPLETED"
        update_batch_job(
            db_manager=db_manager,
            batch_job_name=batch_job_name,
            status=job_status,
        )
        logger.info(f"Batch job '{batch_job_name}' status updated to {job_status}")
    except Exception:
        # Any unhandled exceptions will be caught here
        job_status = "FAILURE"
        logger.error(f"Batch job '{batch_job_name}' failed to complete")
        update_batch_job(
            db_manager=db_manager,
            batch_job_name=batch_job_name,
            status=job_status,
        )
        logger.info(f"Batch job '{batch_job_name}' status updated to {job_status}")
        sys.exit(1)
