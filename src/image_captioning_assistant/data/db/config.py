import os
from dataclasses import dataclass

from image_captioning_assistant.aws.get_secret import get_secret


@dataclass
class Config:

    db_writer_host: str
    db_reader_host: str
    db_port: str = "5432"
    db_name: str = "postgres"

    @classmethod
    def get_db_credentials(cls):
        if os.environ.get("ENVIRONMENT") == "production":
            return {
                "user": os.environ["DB_USER"],
                "password": os.environ["DB_PASSWORD"],
            }
        else:
            DB_SECRET_NAME = os.environ["DB_SECRET_NAME"]
            AWS_REGION = os.environ["AWS_REGION"]
            credentials = get_secret(secret_name=DB_SECRET_NAME, region_name=AWS_REGION)
            return {
                "user": credentials["username"],
                "password": credentials["password"],
            }

    def get_writer_database_url(self):
        creds = self.get_db_credentials()
        return f"postgresql://{creds['user']}:{creds['password']}@{self.db_writer_host}:{self.db_port}/{self.db_name}"

    def get_reader_database_url(self):
        creds = self.get_db_credentials()
        return f"postgresql://{creds['user']}:{creds['password']}@{self.db_reader_host}:{self.db_port}/{self.db_name}"
