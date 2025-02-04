from datetime import datetime

from loguru import logger

from image_captioning_assistant.data.db.config import Config
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.models import BatchJob
from image_captioning_assistant.data.db.utils import create_tables_if_not_exist


def create_batch_job(
    db_manager: DatabaseManager,
    start_time: datetime,
    s3_bucket: str,
    s3_prefix: str,
    status: str,
):
    with db_manager.get_writer_db() as db:
        new_job = BatchJob(
            start_time=start_time,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
            status=status,
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        return new_job


def get_batch_job(db_manager: DatabaseManager, batch_job_name: str):
    with db_manager.get_reader_db() as db:
        return (
            db.query(BatchJob).filter(BatchJob.batch_job_name == batch_job_name).first()
        )


def get_n_batch_jobs(db_manager: DatabaseManager, n: int):
    with db_manager.get_reader_db() as db:
        return (
            db.query(BatchJob).order_by(BatchJob.batch_job_name.desc()).limit(n).all()
        )


def update_batch_job(
    db_manager: DatabaseManager, batch_job_name: str, status: str, end_time: datetime
):
    with db_manager.get_writer_db() as db:
        job = (
            db.query(BatchJob).filter(BatchJob.batch_job_name == batch_job_name).first()
        )
        if job:
            job.status = status
            job.end_time = end_time
            db.commit()
            db.refresh(job)
        return job


def delete_batch_job(db_manager: DatabaseManager, batch_job_name: str):
    with db_manager.get_writer_db() as db:
        job = (
            db.query(BatchJob).filter(BatchJob.batch_job_name == batch_job_name).first()
        )
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
    new_job = create_batch_job(
        db_manager=db_manager,
        start_time=datetime.now(),
        s3_bucket="bucket",
        s3_prefix="prefix/",
        status="STARTED",
    )
    logger.info(f"Created new job with name: {new_job.batch_job_name}")

    logger.info("Retrieving job")
    job = get_batch_job(db_manager, new_job.batch_job_name)
    logger.info(f"Retrieved job: {job.batch_job_name}, Status: {job.status}")

    logger.info("Updating job")
    updated_job = update_batch_job(
        db_manager, new_job.batch_job_name, "COMPLETED", datetime.now()
    )
    logger.info(
        f"Updated job: {updated_job.batch_job_name}, New Status: {updated_job.status}"
    )

    logger.info("\nRetrieving last 5 jobs")
    last_five_jobs = get_n_batch_jobs(db_manager, 10)
    for job in last_five_jobs:
        logger.info(
            f"Job Name: {job.batch_job_name}, Status: {job.status}, Start Time: {job.start_time}"
        )
