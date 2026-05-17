import logging
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url

from piglets.types import Column, Database, QueryResult, SQLQuery, Table

logger = logging.getLogger(__name__)


def connection_to_sqlalchemy_url(connection: Any) -> str:
    if hasattr(connection, "render_as_string"):
        return connection.render_as_string(hide_password=False)
    return connection


def connection_to_create_engine_kwargs(connection: Any) -> dict[str, Any]:
    if hasattr(connection, "create_engine_kwargs"):
        return connection.create_engine_kwargs()
    return {}


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


def database_type_from_connection(connection: Any) -> str:
    connection_url = connection_to_sqlalchemy_url(connection)
    url = make_url(connection_url)
    driver_name = url.drivername.split("+", 1)[0]

    if driver_name == "bigquery":
        return "BigQuery"
    if driver_name == "snowflake":
        return "Snowflake"
    if driver_name == "duckdb":
        database = url.database or ""
        if database.startswith(("md:", "motherduck:")):
            return "MotherDuck"
        return "DuckDB"
    if driver_name == "sqlite":
        return "SQLite"
    if driver_name in {"postgres", "postgresql"}:
        return "PostgreSQL"
    if driver_name == "mysql":
        return "MySQL"

    return driver_name.replace("_", " ").title().replace(" ", "")


class DatabaseConnector():
    """Base class for database connectors."""
    def __init__(
                self, 
                connection: Any
    ):
        connection_url = connection_to_sqlalchemy_url(connection)
        engine_kwargs = connection_to_create_engine_kwargs(connection)
        self.database_name = database_name_from_connection(connection_url)
        self.database_type = database_type_from_connection(connection_url)

        logger.info("Connecting to database %s", self.database_name)
        self.engine = create_engine(connection_url, **engine_kwargs)
        self.inspector = inspect(self.engine)

    def get_database_schema(self) -> Database:
        """Returns the schema of the database."""
        tables = []
        for table_name in self.inspector.get_table_names():
            columns = []
            for column_info in self.inspector.get_columns(table_name):
                # TODO: Populate column descriptions when metadata retrieval supports them.
                column = Column(name=column_info["name"], data_type=str(column_info["type"]))
                columns.append(column)
            table = Table(name=table_name, columns=columns)
            tables.append(table)
        return Database(
            name=self.database_name,
            database_type=self.database_type,
            tables=tables,
        )
    
    def execute_query(self, query: SQLQuery | str) -> QueryResult:
        """Execute a SQL query and return a typed result."""
        sql = query if isinstance(query, str) else query.query
        if not sql.strip():
            raise ValueError("query must not be empty")

        with self.engine.connect() as connection:
            result = connection.execute(text(sql))
            columns = list(result.keys())
            rows = [tuple(row) for row in result.fetchall()]

        return QueryResult(
            query=sql,
            columns=columns,
            rows=rows,
            row_count=len(rows),
        )
