from loguru import logger
from sqlalchemy.sql import select

from image_captioning_assistant.aurora_db.client import AuroraServerlessClient
from image_captioning_assistant.aurora_db.models import image_metadata, job


class DatabaseOperations:
    def __init__(
        self, cluster_arn: str, secret_arn: str, database_name: str, region_name: str
    ):
        self.client = AuroraServerlessClient(region_name)
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database_name = database_name

    def _execute_statement(self, sql_query):
        try:
            return self.client.execute_statement(
                self.cluster_arn, self.secret_arn, self.database_name, sql_query
            )
        except Exception as e:
            logger.error(f"Error executing SQL statement: {e}")
            raise

    def insert_job(self, job_id: str, start_time: str, status: str, end_time: str):
        sql_query = f"""
        INSERT INTO job (job_id, start_time, status, end_time)
        VALUES ({job_id}, '{start_time}', '{status}', '{end_time}')
        """
        return self._execute_statement(sql_query)

    def insert_image_metadata(
        self,
        job_id: str,
        image_id: str,
        description: str,
        transcription: str,
        people_and_groups: str,
        date: str,
    ):
        sql = f"""
        INSERT INTO image_metadata (job_id, image_id, description, transcription, people_and_groups, date)
        VALUES ({job_id}, '{image_id}', '{description}', '{transcription}', '{people_and_groups}', '{date}')
        """
        return self._execute_statement(sql)

    def get_job_by_id(self, job_id: str):
        sql = select([job]).where(job.c.job_id == job_id)
        return self._execute_statement(str(sql))

    def get_image_metadata_by_job_id(self, job_id: str):
        sql = select([image_metadata]).where(image_metadata.c.job_id == job_id)
        return self._execute_statement(str(sql))

    def update_job_status(self, job_id: str, new_status: str):
        sql = f"""
        UPDATE job
        SET status = '{new_status}'
        WHERE job_id = {job_id}
        """
        return self._execute_statement(sql)

    def delete_job(self, job_id: str):
        sql = f"DELETE FROM job WHERE job_id = {job_id}"
        return self._execute_statement(sql)

    def delete_image_metadata(self, image_id: str):
        sql = f"DELETE FROM image_metadata WHERE image_id = '{image_id}'"
        return self._execute_statement(sql)

    def get_jobs_by_status(self, status: str):
        sql = select([job]).where(job.c.status == status)
        return self._execute_statement(str(sql))

    def get_image_metadata_by_date_range(self, start_date: str, end_date: str):
        sql = select([image_metadata]).where(
            (image_metadata.c.date >= start_date) & (image_metadata.c.date <= end_date)
        )
        return self._execute_statement(str(sql))

    def count_jobs_by_status(self):
        sql = """
        SELECT status, COUNT(*) as count
        FROM job
        GROUP BY status
        """
        return self._execute_statement(sql)
