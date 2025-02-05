from loguru import logger
from sqlalchemy import inspect, text

from image_captioning_assistant.data.db.models import Base


def create_tables_if_not_exist(engine) -> None:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Get all table names defined in your models
    model_tables = Base.metadata.tables.keys()

    # Check each model table
    for table_name in model_tables:
        if table_name not in existing_tables:
            logger.info(f"Creating table: {table_name}")
            Base.metadata.tables[table_name].create(engine)
        else:
            logger.info(f"Table already exists: {table_name}")


def reset_tables(engine) -> None:
    # Disable foreign key checks (for PostgreSQL)
    with engine.connect() as connection:
        connection.execute(text("SET CONSTRAINTS ALL DEFERRED;"))

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Drop all existing tables with CASCADE
    for table_name in existing_tables:
        logger.info(f"Dropping table: {table_name}")
        with engine.connect() as connection:
            connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;'))
            connection.commit()

    # Recreate all tables based on current model definitions
    logger.info("Recreating all tables")
    Base.metadata.create_all(engine)

    # Re-enable foreign key checks (for PostgreSQL)
    with engine.connect() as connection:
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE;"))

    logger.info("All tables have been reset")
