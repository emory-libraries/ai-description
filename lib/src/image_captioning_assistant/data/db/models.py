# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "document"
    document_id = Column(String(100), primary_key=True)
    image_id = Column(String(100))


class BatchJob(Base):
    __tablename__ = "batch_job"
    batch_job_name = Column(String(100), primary_key=True)
    s3_bucket = Column(String(50))
    s3_prefix = Column(String(50))
    start_time = Column(DateTime)
    status = Column(String(50))
    end_time = Column(DateTime)


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    metadata_id = Column(Integer, primary_key=True)
    batch_job_name = Column(Integer, ForeignKey("batch_job.batch_job_name"))
    document_id = Column(String(100), ForeignKey("document.document_id"))
    description = Column(String(500))
    transcription = Column(String(1000))
    people_and_groups = Column(String(500))
    date = Column(DateTime)
    location = Column(String(500))
    publication_info = Column(String(500))
    contextual_info = Column(String(500))
    bias_id = Column(Integer, ForeignKey("document_bias.bias_id"))


class DocumentBias(Base):
    __tablename__ = "document_bias"
    bias_id = Column(Integer, primary_key=True)
    batch_job_name = Column(Integer, ForeignKey("batch_job.batch_job_name"))
    document_id = Column(String(100))
    bias_type = Column(String(500))
    bias_level = Column(String(1000))
    explanation = Column(String(500))
