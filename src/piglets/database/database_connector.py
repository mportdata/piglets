import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, URL

from piglets.types import Column, Database, Table

logger = logging.getLogger(__name__)

class DatabaseConnector():
    """Base class for database connectors."""
    def __init__(
                self, 
                database_type: str, 
                database_name: str,              
                username: str = None,
                password: str = None, 
                host: str = None,
                port: int = None,
                database: str = None,
                gcp_project_id: str = None
    ):
        if database_type == "bigquery":
            if not host:
                if gcp_project_id:
                    host = gcp_project_id
                else:
                    load_dotenv()
                    google_cloud_project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", None)
                    host = google_cloud_project_id
            if not host:
                raise ValueError("gcp_project_id must be provided for BigQuery databases.")

        connection_url = URL.create(
            drivername=database_type,
            username=username,
            password=password,
            host=host,
            port=port,
            database=database_name
        )
        logger.info(f"Connecting to database with URL: {connection_url}")
        self.engine = create_engine(connection_url)
        self.inspector = inspect(self.engine)
        self.database_name = database_name

    def get_database_schema(self) -> Database:
        """Returns the schema of the database."""
        tables = []
        for table_name in self.inspector.get_table_names():
            columns = []
            for column_info in self.inspector.get_columns(table_name):
                column = Column(name=column_info["name"], data_type=str(column_info["type"]))
                columns.append(column)
            table = Table(name=table_name, columns=columns)
            tables.append(table)
        return Database(name=self.database_name, tables=tables)
    
     # TODO: Implement database querying methods using connector-x or similar libraries for efficient querying and data retrieval.
