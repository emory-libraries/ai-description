from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy.exc import NoResultFound

from image_captioning_assistant.data.db.config import Config
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.models import DocumentMetadata
from image_captioning_assistant.data.db.utils import create_tables_if_not_exist


def create_document_metadata(
    db_manager: DatabaseManager,
    batch_job_name: str,
    document_id: str,
    description: Optional[str] = None,
    transcription: Optional[str] = None,
    people_and_groups: Optional[str] = None,
    date: Optional[datetime] = None,
    location: Optional[str] = None,
    publication_info: Optional[str] = None,
    contextual_info: Optional[str] = None,
):
    with db_manager.get_writer_db() as db:
        new_metadata = DocumentMetadata(
            batch_job_name=batch_job_name,
            document_id=document_id,
            description=description,
            transcription=transcription,
            people_and_groups=people_and_groups,
            date=date,
            location=location,
            publication_info=publication_info,
            contextual_info=contextual_info,
        )
        db.add(new_metadata)
        db.commit()
        db.refresh(new_metadata)
        return new_metadata


def get_document_metadata(db_manager: DatabaseManager, metadata_id: int):
    with db_manager.get_reader_db() as db:
        return (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.metadata_id == metadata_id)
            .first()
        )


def get_document_metadata_by_document_id(db_manager: DatabaseManager, document_id: str):
    with db_manager.get_reader_db() as db:
        return (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == document_id)
            .all()
        )


def get_document_metadata_by_id_and_job(
    db_manager: DatabaseManager, document_id: str, batch_job_name: str
):
    with db_manager.get_reader_db() as db:
        try:
            return (
                db.query(DocumentMetadata)
                .filter(DocumentMetadata.document_id == document_id)
                .filter(DocumentMetadata.batch_job_name == batch_job_name)
                .one()
            )
        except NoResultFound:
            return None


def update_document_metadata(
    db_manager: DatabaseManager,
    metadata_id: int,
    description: Optional[str] = None,
    transcription: Optional[str] = None,
    people_and_groups: Optional[str] = None,
    date: Optional[datetime] = None,
    location: Optional[str] = None,
    publication_info: Optional[str] = None,
    contextual_info: Optional[str] = None,
):
    with db_manager.get_writer_db() as db:
        metadata = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.metadata_id == metadata_id)
            .first()
        )
        if metadata:
            if description is not None:
                metadata.description = description
            if transcription is not None:
                metadata.transcription = transcription
            if people_and_groups is not None:
                metadata.people_and_groups = people_and_groups
            if date is not None:
                metadata.date = date
            if location is not None:
                metadata.location = location
            if publication_info is not None:
                metadata.publication_info = publication_info
            if contextual_info is not None:
                metadata.contextual_info = contextual_info
            db.commit()
            db.refresh(metadata)
        return metadata


def delete_document_metadata(db_manager: DatabaseManager, metadata_id: int):
    with db_manager.get_writer_db() as db:
        metadata = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.metadata_id == metadata_id)
            .first()
        )
        if metadata:
            db.delete(metadata)
            db.commit()
        return metadata


def delete_document_metadata_by_id_and_job(
    db_manager: DatabaseManager, document_id: str, batch_job_name: str
):
    with db_manager.get_writer_db() as db:
        deleted_count = (
            db.query(DocumentMetadata)
            .filter(DocumentMetadata.document_id == document_id)
            .filter(DocumentMetadata.batch_job_name == batch_job_name)
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_count


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

    logger.info("Creating document metadata")
    new_metadata = create_document_metadata(
        db_manager,
        batch_job_name="job1",
        document_id="doc123",
        description="Sample document",
        transcription="This is a sample transcription",
        people_and_groups="John Doe, Jane Smith",
        date=datetime.now(),
        location="New York, NY",
        publication_info="Sample Publisher, 2023",
        contextual_info="Additional context about the document",
    )
    logger.info(f"Created new document metadata with ID: {new_metadata.metadata_id}")

    logger.info("Retrieving document metadata")
    metadata = get_document_metadata(db_manager, new_metadata.metadata_id)
    logger.info(
        f"Retrieved metadata: {metadata.metadata_id}, Description: {metadata.description}"
    )

    logger.info("Updating document metadata")
    updated_metadata = update_document_metadata(
        db_manager,
        new_metadata.metadata_id,
        description="Updated sample document",
        location="Los Angeles, CA",
    )
    logger.info(
        f"Updated metadata: {updated_metadata.metadata_id}, New Description: {updated_metadata.description}"
    )

    logger.info("Retrieving document metadata by document ID")
    doc_metadata = get_document_metadata_by_document_id(db_manager, "doc123")
    for metadata in doc_metadata:
        logger.info(
            f"Metadata ID: {metadata.metadata_id}, Document ID: {metadata.document_id}"
        )

    logger.info("Deleting document metadata")
    deleted_metadata = delete_document_metadata(db_manager, new_metadata.metadata_id)
    if deleted_metadata:
        logger.info(f"Deleted metadata with ID: {deleted_metadata.metadata_id}")
    else:
        logger.info("No metadata found to delete")
