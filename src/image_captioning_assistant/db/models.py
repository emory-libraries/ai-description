from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table

from image_captioning_assistant.data.constants import (
    JOB_ID,
    IMAGE_ID,
    DESCRIPTION,
    TRANSCRIPTION,
    METADATA_ID,
    DOCUMENT_ID,
    START_TIME,
    STATUS,
    END_TIME,
    PEOPLE_AND_GROUPS,
    PUBLICATION_INFO,
    DATE,
    LOCATION,
    CONTEXTUAL_INFO,
    BIAS_ID,
    BIAS_LEVEL,
    BIAS_TYPE,
    EXPLANATION,
    JOB_TABLE,
    METADATA_TABLE,
    BIAS_TABLE,
    DOCUMENT_TABLE,
)

metadata = MetaData()

job = Table(
    JOB_TABLE,
    metadata,
    Column(JOB_ID, Integer, primary_key=True),
    Column(START_TIME, DateTime),
    Column(STATUS, String(50)),
    Column(END_TIME, DateTime),
)

document_metadata = Table(
    DOCUMENT_TABLE,
    metadata,
    Column(DOCUMENT_ID, String(100), primary_key=True),
    Column(IMAGE_ID, String(100)),
)

document_metadata = Table(
    METADATA_TABLE,
    metadata,
    Column(METADATA_ID, Integer, primary_key=True),
    Column(JOB_ID, Integer, ForeignKey(f"{JOB_TABLE}.{JOB_ID}")),
    Column(DOCUMENT_ID, Integer, ForeignKey(f"{DOCUMENT_TABLE}.{DOCUMENT_ID}")),
    Column(DESCRIPTION, String(500)),
    Column(TRANSCRIPTION, String(1000)),
    Column(PEOPLE_AND_GROUPS, String(500)),
    Column(DATE, DateTime),
    Column(LOCATION, String(500)),
    Column(PUBLICATION_INFO, String(500)),
    Column(CONTEXTUAL_INFO, String(500)),
    Column(BIAS_ID, Integer, ForeignKey(f"{BIAS_TABLE}.{BIAS_ID}")),
)

document_bias = Table(
    BIAS_TABLE,
    metadata,
    Column(BIAS_ID, Integer, primary_key=True),
    Column(JOB_ID, Integer, ForeignKey(f"{JOB_TABLE}.{JOB_ID}")),
    Column(DOCUMENT_ID, String(100)),
    Column(BIAS_TYPE, String(500)),
    Column(BIAS_LEVEL, String(1000)),
    Column(EXPLANATION, String(500)),
)
