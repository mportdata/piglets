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
                database: str = None,              
                username: str = None,
                password: str = None, 
                host: str = None,
                port: int = None,

                gcp_project_id: str = None,
                bq_dataset: str = None,

                snowflake_account: str = None,
                snowflake_region: str = None,
                snowflake_database: str = None,
                snowflake_schema: str = None,
                
                protocol: str = None
    ):
        if database_type == "snowflake":
            from snowflake.sqlalchemy import URL as sf_url
            if not snowflake_account:
                load_dotenv()
                snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT", None)
            if not snowflake_account:
                raise ValueError("snowflake_account must be provided for Snowflake databases.")
            if not snowflake_database:
                raise ValueError("snowflake_database must be provided for Snowflake databases.")
            if not username:
                load_dotenv()
                username = os.getenv("SNOWFLAKE_USER", None)
            if not username:
                raise ValueError("Username must be provided for Snowflake databases, either as an argument or as SNOWFLAKE_USER in environment variables.")
            if not password:
                load_dotenv()
                password = os.getenv("SNOWFLAKE_PASSWORD", None)
            if not password:
                raise ValueError("Password must be provided for Snowflake databases, either as an argument or as SNOWFLAKE_PASSWORD in environment variables.")

            connection_url = sf_url(
                account=snowflake_account,
                region=snowflake_region or "",
                user=username,
                password=password,
                database=snowflake_database,
                schema=snowflake_schema,
                port=port or 443,
                protocol=protocol or "https",
                host=host or f"{snowflake_account}.snowflakecomputing.com"
            )

            if snowflake_schema:
                self.database_name = f"{snowflake_database}.{snowflake_schema}"
            else:
                self.database_name = snowflake_database

        else:
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
                if not database:
                    database = bq_dataset
                if not database:
                    raise ValueError("bq_dataset must be provided for BigQuery databases.")

            connection_url = URL.create(
                drivername=database_type,
                username=username,
                password=password,
                host=host,
                port=port,
                database=database
            )

            self.database_name = database

        logger.info("Connecting to %s database %s", database_type, self.database_name)
        self.engine = create_engine(connection_url)
        self.inspector = inspect(self.engine)

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
