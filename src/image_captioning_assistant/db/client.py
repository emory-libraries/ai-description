import time

import boto3
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)


class AuroraServerlessClient:
    def __init__(self, region_name):
        self.client = boto3.client("rds-data", region_name=region_name)
        self.rds_client = boto3.client("rds", region_name=region_name)

    def create_db_cluster(
        self, cluster_name, engine, engine_version, master_username, master_password
    ):
        response = self.rds_client.create_db_cluster(
            DBClusterIdentifier=cluster_name,
            Engine=engine,
            EngineVersion=engine_version,
            EngineMode="serverless",
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            ScalingConfiguration={
                "MinCapacity": 1,
                "MaxCapacity": 16,
                "AutoPause": True,
                "SecondsUntilAutoPause": 300,
            },
        )
        return response

    def delete_db_cluster(self, cluster_name):
        response = self.rds_client.delete_db_cluster(
            DBClusterIdentifier=cluster_name, SkipFinalSnapshot=True
        )
        return response

    def describe_db_cluster(self, cluster_name):
        response = self.rds_client.describe_db_clusters(
            DBClusterIdentifier=cluster_name
        )
        return response["DBClusters"][0]

    def wait_for_cluster_available(self, cluster_name, timeout=600):
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    "Cluster did not become available within the specified timeout."
                )

            cluster_info = self.describe_db_cluster(cluster_name)
            if cluster_info["Status"] == "available":
                return cluster_info
            time.sleep(30)

    def execute_statement(self, cluster_arn, secret_arn, database_name, sql_statement):
        response = self.client.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=sql_statement,
        )
        return response

    def create_tables(self, cluster_arn, secret_arn, database_name):
        engine = create_engine("postgresql://")
        for table in metadata.sorted_tables:
            create_stmt = str(table.compile(engine))
            self.execute_statement(cluster_arn, secret_arn, database_name, create_stmt)
        print("Tables created successfully")

    def insert_job(
        self,
        cluster_arn,
        secret_arn,
        database_name,
        job_id,
        start_time,
        status,
        end_time,
    ):
        sql = f"""
        INSERT INTO job (job_id, start_time, status, end_time)
        VALUES ({job_id}, '{start_time}', '{status}', '{end_time}')
        """
        return self.execute_statement(cluster_arn, secret_arn, database_name, sql)

    def insert_image_metadata(
        self,
        cluster_arn,
        secret_arn,
        database_name,
        job_id,
        image_id,
        description,
        transcription,
        people_and_groups,
        date,
    ):
        sql = f"""
        INSERT INTO image_metadata (job_id, image_id, description, transcription, people_and_groups, date)
        VALUES ({job_id}, '{image_id}', '{description}', '{transcription}', '{people_and_groups}', '{date}')
        """
        return self.execute_statement(cluster_arn, secret_arn, database_name, sql)


# Usage example
if __name__ == "__main__":
    # Initialize the client
    aurora_client = AuroraServerlessClient("us-west-2")

    # SQLAlchemy setup
    metadata = MetaData()

    # Define the job table
    job_table = Table(
        "job",
        metadata,
        Column("job_id", Integer, primary_key=True),
        Column("start_time", DateTime),
        Column("status", String(50)),
        Column("end_time", DateTime),
    )

    # Define the image_metadata table
    image_metadata_table = Table(
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

    # Create a new Aurora Serverless cluster
    cluster_name = "my-aurora-serverless"
    create_response = aurora_client.create_db_cluster(
        cluster_name, "aurora-postgresql", "11.9", "admin", "your-password-here"
    )
    print("Cluster creation initiated:", create_response)

    # Wait for the cluster to become available
    cluster_info = aurora_client.wait_for_cluster_available(cluster_name)
    print("Cluster is now available:", cluster_info)

    # Get cluster ARN and secret ARN
    cluster_arn = cluster_info["DBClusterArn"]
    secret_arn = cluster_info["SecretArn"]

    # Create tables
    aurora_client.create_tables(cluster_arn, secret_arn, "postgres")

    # Insert sample data
    aurora_client.insert_job(
        cluster_arn,
        secret_arn,
        "postgres",
        1,
        "2023-05-01 10:00:00",
        "completed",
        "2023-05-01 11:00:00",
    )
    aurora_client.insert_image_metadata(
        cluster_arn,
        secret_arn,
        "postgres",
        1,
        "image1.jpg",
        "A beautiful landscape",
        "Mountain view",
        "Nature enthusiasts",
        "2023-05-01 10:30:00",
    )

    print("Sample data inserted successfully")

    # Don't forget to delete the cluster when you're done
    # delete_response = aurora_client.delete_db_cluster(cluster_name)
    # print("Cluster deletion initiated:", delete_response)
