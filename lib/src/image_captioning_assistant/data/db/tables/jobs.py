# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from datetime import datetime

from image_captioning_assistant.data.db.config import Config
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.models import BatchJob
from image_captioning_assistant.data.db.utils import create_tables_if_not_exist
from loguru import logger


def create_job(start_time: datetime, status: str):
    with db_manager.get_writer_db() as db:
        new_job = BatchJob(start_time=start_time, status=status)
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job


def get_job(job_id: int):
    with db_manager.get_reader_db() as db:
        return db.query(BatchJob).filter(BatchJob.job_id == job_id).first()


def get_n_jobs(n: int):
    with db_manager.get_reader_db() as db:
        return db.query(BatchJob).order_by(BatchJob.job_id.desc()).limit(n).all()


def update_job(job_id: int, status: str, end_time: datetime):
    with db_manager.get_writer_db() as db:
        job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
        if job:
            job.status = status
            job.end_time = end_time
            db.commit()
            db.refresh(job)
        return job


def delete_job(job_id: int):
    with db_manager.get_writer_db() as db:
        job = db.query(BatchJob).filter(BatchJob.job_id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
        return job


if __name__ == "__main__":
    # Example usage:
    import os

    from dotenv import load_dotenv

    load_dotenv()

    config = Config(
        db_port=os.environ["DB_PORT"],
        db_name=os.environ["DB_NAME"],
        db_writer_host=os.environ["DB_WRITER_HOST"],
        db_reader_host=os.environ["DB_READER_HOST"],
    )
    db_manager = DatabaseManager(config)
    create_tables_if_not_exist(db_manager.writer_engine)
    logger.info("Creating job")
    new_job = create_job(datetime.now(), "STARTED")
    logger.info(f"Created new job with ID: {new_job.job_id}")

    logger.info("Retrieving job")
    job = get_job(new_job.job_id)
    logger.info(f"Retrieved job: {job.job_id}, Status: {job.status}")

    logger.info("Updating job")
    updated_job = update_job(new_job.job_id, "COMPLETED", datetime.now())
    logger.info(f"Updated job: {updated_job.job_id}, New Status: {updated_job.status}")

    logger.info("\nRetrieving last 5 jobs")
    last_five_jobs = get_n_jobs(5)
    for job in last_five_jobs:
        logger.info(f"Job ID: {job.job_id}, Status: {job.status}, Start Time: {job.start_time}")
