# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

from contextlib import contextmanager

from image_captioning_assistant.data.db.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DatabaseManager:
    def __init__(self, config: Config):
        self.writer_engine = create_engine(config.get_writer_database_url())
        self.reader_engine = create_engine(config.get_reader_database_url())
        self.WriterSession = sessionmaker(bind=self.writer_engine)
        self.ReaderSession = sessionmaker(bind=self.reader_engine)

    @contextmanager
    def get_writer_db(self):
        db = self.WriterSession()
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def get_reader_db(self):
        db = self.ReaderSession()
        try:
            yield db
        finally:
            db.close()
