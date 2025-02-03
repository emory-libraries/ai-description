from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table

metadata = MetaData()

job = Table(
    "job",
    metadata,
    Column("job_id", Integer, primary_key=True),
    Column("start_time", DateTime),
    Column("status", String(50)),
    Column("end_time", DateTime),
)

image_metadata = Table(
    "image_metadata",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("job.job_id")),
    Column("image_id", String(100)),
    Column("description", String(500)),
    Column("transcription", String(1000)),
    Column("people_and_groups", String(500)),
    Column("date", DateTime),
)
