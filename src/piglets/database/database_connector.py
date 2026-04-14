import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

from piglets.types import Column, Database, Table

load_dotenv()

class DatabaseConnector():
    """Base class for database connectors."""
    def __init__(self, database_type: str, database_name: str, gcp_project_id: str = None):
        if database_type == "bigquery":
            google_cloud_project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", None)
            if not gcp_project_id and not google_cloud_project_id:
                    raise ValueError("GCP project ID must be provided for BigQuery databases.")
            else:
                 self.database_name = database_name
                 connection_string = f"{database_type}://{gcp_project_id or google_cloud_project_id}/{database_name}"
                 self.engine = create_engine(connection_string)
                 self.inspector = inspect(self.engine)
        else:
             raise ValueError("Currently supported database_type's: `bigquery`")

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
