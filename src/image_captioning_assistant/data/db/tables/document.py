from loguru import logger

from image_captioning_assistant.data.db.config import Config
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.data.db.models import Document
from image_captioning_assistant.data.db.utils import create_tables_if_not_exist


def create_document(db_manager: DatabaseManager, document_id: str, image_id: str):
    with db_manager.get_writer_db() as db:
        new_document = Document(document_id=document_id, image_id=image_id)
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        return new_document


def get_document(db_manager: DatabaseManager, document_id: str):
    with db_manager.get_reader_db() as db:
        return db.query(Document).filter(Document.document_id == document_id).first()


def get_n_documents(db_manager: DatabaseManager, n: int):
    with db_manager.get_reader_db() as db:
        return db.query(Document).order_by(Document.document_id.desc()).limit(n).all()


def update_document(db_manager: DatabaseManager, document_id: str, new_image_id: str):
    with db_manager.get_writer_db() as db:
        document = (
            db.query(Document).filter(Document.document_id == document_id).first()
        )
        if document:
            document.image_id = new_image_id
            db.commit()
            db.refresh(document)
        return document


def put_document(db_manager: DatabaseManager, document_id: str, image_id: str):
    with db_manager.get_writer_db() as db:
        document = (
            db.query(Document).filter(Document.document_id == document_id).first()
        )
        if document:
            # Update existing document
            document.image_id = image_id
            logger.info(f"Updated existing document: Document ID: {document_id}")
        else:
            # Create new document
            document = Document(document_id=document_id, image_id=image_id)
            db.add(document)
            logger.info(f"Created new document: Document ID: {document_id}")

        db.commit()
        db.refresh(document)
        return document


def delete_document(db_manager: DatabaseManager, document_id: str):
    with db_manager.get_writer_db() as db:
        document = (
            db.query(Document).filter(Document.document_id == document_id).first()
        )
        if document:
            db.delete(document)
            db.commit()
        return document


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

    logger.info("Creating document")
    new_doc = create_document(db_manager, "doc123", "img456")
    logger.info(
        f"Created new document: Document ID: {new_doc.document_id}, Image ID: {new_doc.image_id}"
    )

    logger.info("Retrieving document")
    doc = get_document(db_manager, "doc123")
    logger.info(
        f"Retrieved document: Document ID: {doc.document_id}, Image ID: {doc.image_id}"
    )

    logger.info("Updating document")
    updated_doc = update_document(db_manager, "doc123", "new_img789")
    logger.info(
        f"Updated document: Document ID: {updated_doc.document_id}, New Image ID: {updated_doc.image_id}"
    )

    logger.info("\nRetrieving 5 documents")
    n_docs = get_n_documents(db_manager, 5)
    for idx, doc in enumerate(n_docs):
        logger.info(f"{idx} - Document ID: {doc.document_id}, Image ID: {doc.image_id}")
