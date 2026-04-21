import logging
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url

from piglets.types import Column, Database, Table

logger = logging.getLogger(__name__)


def connection_to_sqlalchemy_url(connection: Any) -> str:
    if hasattr(connection, "render_as_string"):
        return connection.render_as_string(hide_password=False)
    return connection


def database_name_from_connection(connection: Any) -> str:
    connection_url = connection_to_sqlalchemy_url(connection)
    url = make_url(connection_url)

    if url.drivername == "bigquery":
        if url.host and url.database:
            return f"{url.host}:{url.database}"
        if url.host:
            return url.host
        if url.database:
            return url.database
        return "bigquery"

    if url.drivername == "snowflake":
        if url.database:
            return url.database.replace("/", ".")
        return url.host or "snowflake"

    if url.drivername == "duckdb":
        return url.database or ":memory:"

    return url.database or url.host or url.drivername


def database_name_from_connection_string(connection_string: str) -> str:
    return database_name_from_connection(connection_string)


class DatabaseConnector():
    """Base class for database connectors."""
    def __init__(
                self, 
                connection: Any
    ):
        connection_url = connection_to_sqlalchemy_url(connection)
        self.database_name = database_name_from_connection(connection_url)

        logger.info("Connecting to database %s", self.database_name)
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
