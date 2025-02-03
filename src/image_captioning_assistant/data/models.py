from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = 'job'
    job_id = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    status = Column(String(50))
    end_time = Column(DateTime)

class DocumentMetadata(Base):
    __tablename__ = 'document_metadata'
    document_id = Column(String(100), primary_key=True)
    image_id = Column(String(100))

class Metadata(Base):
    __tablename__ = 'metadata'
    metadata_id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.job_id'))
    document_id = Column(String(100), ForeignKey('document_metadata.document_id'))
    description = Column(String(500))
    transcription = Column(String(1000))
    people_and_groups = Column(String(500))
    date = Column(DateTime)
    location = Column(String(500))
    publication_info = Column(String(500))
    contextual_info = Column(String(500))
    bias_id = Column(Integer, ForeignKey('document_bias.bias_id'))

class DocumentBias(Base):
    __tablename__ = 'document_bias'
    bias_id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.job_id'))
    document_id = Column(String(100))
    bias_type = Column(String(500))
    bias_level = Column(String(1000))
    explanation = Column(String(500))
