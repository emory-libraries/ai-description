# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from typing import Optional

from image_captioning_assistant.data.db.config import Config
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.models import DocumentBias
from image_captioning_assistant.data.db.utils import create_tables_if_not_exist
from loguru import logger


def create_document_bias(
    db_manager: DatabaseManager,
    batch_job_name: str,
    document_id: str,
    bias_type: str,
    bias_level: str,
    explanation: Optional[str] = None,
):
    with db_manager.get_writer_db() as db:
        new_bias = DocumentBias(
            batch_job_name=batch_job_name,
            document_id=document_id,
            bias_type=bias_type,
            bias_level=bias_level,
            explanation=explanation,
        )
        db.add(new_bias)
        db.commit()
        db.refresh(new_bias)
        return new_bias


def get_document_bias(db_manager: DatabaseManager, bias_id: int):
    with db_manager.get_reader_db() as db:
        return db.query(DocumentBias).filter(DocumentBias.bias_id == bias_id).first()


def get_document_bias_by_document_id(db_manager: DatabaseManager, document_id: str):
    with db_manager.get_reader_db() as db:
        return db.query(DocumentBias).filter(DocumentBias.document_id == document_id).all()


def update_document_bias(
    db_manager: DatabaseManager,
    bias_id: int,
    bias_type: Optional[str] = None,
    bias_level: Optional[str] = None,
    explanation: Optional[str] = None,
):
    with db_manager.get_writer_db() as db:
        bias = db.query(DocumentBias).filter(DocumentBias.bias_id == bias_id).first()
        if bias:
            if bias_type is not None:
                bias.bias_type = bias_type
            if bias_level is not None:
                bias.bias_level = bias_level
            if explanation is not None:
                bias.explanation = explanation
            db.commit()
            db.refresh(bias)
        return bias


def delete_document_bias(db_manager: DatabaseManager, bias_id: int):
    with db_manager.get_writer_db() as db:
        bias = db.query(DocumentBias).filter(DocumentBias.bias_id == bias_id).first()
        if bias:
            db.delete(bias)
            db.commit()
        return bias


def clear_document_bias_by_job_and_document(db_manager: DatabaseManager, batch_job_name: str, document_id: str):
    with db_manager.get_writer_db() as db:
        deleted_rows = (
            db.query(DocumentBias)
            .filter(
                DocumentBias.batch_job_name == batch_job_name,
                DocumentBias.document_id == document_id,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return deleted_rows


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

    logger.info("Creating document bias")
    new_bias = create_document_bias(
        db_manager=db_manager,
        batch_job_name="job1",
        document_id="doc123",
        bias_type="Political",
        bias_level="Moderate",
        explanation="This document shows a moderate level of political bias.",
    )
    logger.info(f"Created new document bias with ID: {new_bias.bias_id}")

    logger.info("Retrieving document bias")
    bias = get_document_bias(db_manager, new_bias.bias_id)
    logger.info(f"Retrieved bias: {bias.bias_id}, Type: {bias.bias_type}, Level: {bias.bias_level}")

    logger.info("Updating document bias")
    updated_bias = update_document_bias(
        db_manager,
        new_bias.bias_id,
        bias_level="High",
        explanation="Upon further review, this document shows a high level of political bias.",
    )
    logger.info(f"Updated bias: {updated_bias.bias_id}, New Level: {updated_bias.bias_level}")

    logger.info("Retrieving document bias by document ID")
    doc_biases = get_document_bias_by_document_id(db_manager, "doc123")
    for doc_bias in doc_biases:
        logger.info(f"Bias ID: {doc_bias.bias_id}, Document ID: {doc_bias.document_id}, Type: {doc_bias.bias_type}")

    logger.info("Deleting document bias")
    deleted_bias = delete_document_bias(db_manager, new_bias.bias_id)
    if deleted_bias:
        logger.info(f"Deleted bias with ID: {deleted_bias.bias_id}")
    else:
        logger.info("No bias found to delete")
