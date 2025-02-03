from sqlalchemy.orm import Session
from datetime import datetime
from load_dotenv import load_dotenv

load_dotenv()

from image_captioning_assistant.data.models import Job, DocumentMetadata, Metadata, DocumentBias
from image_captioning_assistant.data.database import get_db

def create_job(db: Session, start_time: datetime, status: str):
    new_job = Job(start_time=start_time, status=status)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

def get_job(db: Session, job_id: int):
    return db.query(Job).filter(Job.job_id == job_id).first()

def update_job(db: Session, job_id: int, status: str, end_time: datetime):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job:
        job.status = status
        job.end_time = end_time
        db.commit()
        db.refresh(job)
    return job

def delete_job(db: Session, job_id: int):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if job:
        db.delete(job)
        db.commit()
    return job


if __name__ == "__main__":

    db = next(get_db())
    
    # Example usage:
    new_job = create_job(db, datetime.now(), "STARTED")
    print(f"Created new job with ID: {new_job.job_id}")
    
    job = get_job(db, new_job.job_id)
    print(f"Retrieved job: {job.job_id}, Status: {job.status}")
    
    updated_job = update_job(db, new_job.job_id, "COMPLETED", datetime.now())
    print(f"Updated job: {updated_job.job_id}, New Status: {updated_job.status}")
