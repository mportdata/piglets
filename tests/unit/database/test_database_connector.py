import pytest

from sqlalchemy import text
from sqlalchemy.engine import URL

from piglets.database.database_connector import (
    DatabaseConnector,
    database_name_from_connection,
    database_name_from_connection_string,
    database_type_from_connection,
)
from piglets.database.url import BigQueryURL, DuckDBURL, MotherDuckURL, SnowflakeURL
from piglets.types import ProfilingQuery, QueryResult, SearchSpace, SQLQuery


class FakeInspector:
    pass


def test_database_name_from_bigquery_connection(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT_ID", raising=False)

    assert database_name_from_connection(
        BigQueryURL(project_id="project", dataset="dataset")
    ) == "project:dataset"
    assert database_name_from_connection(BigQueryURL(project_id="project")) == "project"
    assert database_name_from_connection(BigQueryURL(dataset="dataset")) == "dataset"
    assert database_name_from_connection(BigQueryURL()) == "bigquery"


def test_database_name_from_bigquery_connection_uses_env_project(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT_ID", "env-project")

    assert database_name_from_connection(BigQueryURL(dataset="dataset")) == "env-project:dataset"
    assert database_name_from_connection(BigQueryURL()) == "env-project"


def test_database_name_from_bigquery_connection_prefers_google_cloud_project(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "google-cloud-project")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT_ID", "google-cloud-project-id")

    assert (
        database_name_from_connection(BigQueryURL(dataset="dataset"))
        == "google-cloud-project:dataset"
    )


def test_database_name_from_snowflake_connection():
    connection = SnowflakeURL(
        account="account",
        user="user",
        password="password",
        database="database",
        schema="schema",
    )

    assert database_name_from_connection(connection) == "database.schema"


def test_database_name_from_duckdb_connection():
    assert database_name_from_connection(DuckDBURL(database="analytics.db")) == "analytics.db"
    assert database_name_from_connection(DuckDBURL()) == ":memory:"


def test_database_name_from_motherduck_connection():
    assert database_name_from_connection(MotherDuckURL(database="analytics")) == "md:analytics"


def test_database_name_from_connection_string_compatibility_alias():
    assert (
        database_name_from_connection_string(
            BigQueryURL(project_id="project", dataset="dataset").render_as_string(
                hide_password=False
            )
        )
        == "project:dataset"
    )


def test_database_name_from_sqlalchemy_url():
    connection = URL.create(drivername="duckdb", database="analytics.db")

    assert database_name_from_connection(connection) == "analytics.db"


def test_database_type_from_known_connections():
    assert (
        database_type_from_connection(BigQueryURL(project_id="project", dataset="dataset"))
        == "BigQuery"
    )
    assert (
        database_type_from_connection(
            SnowflakeURL(
                account="account",
                user="user",
                password="password",
                database="database",
            )
        )
        == "Snowflake"
    )
    assert database_type_from_connection(DuckDBURL(database="analytics.db")) == "DuckDB"
    assert database_type_from_connection(MotherDuckURL(database="analytics")) == "MotherDuck"
    assert database_type_from_connection(URL.create(drivername="sqlite", database="example.db")) == "SQLite"
    assert (
        database_type_from_connection(
            URL.create(drivername="postgresql+psycopg", database="analytics")
        )
        == "PostgreSQL"
    )
    assert (
        database_type_from_connection(
            URL.create(drivername="customdb+driver", database="analytics")
        )
        == "Customdb"
    )


def test_database_connector_accepts_url_builder(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT_ID", raising=False)
    created = {}

    def fake_create_engine(connection):
        created["connection"] = connection
        return object()

    monkeypatch.setattr("piglets.database.database_connector.create_engine", fake_create_engine)
    monkeypatch.setattr("piglets.database.database_connector.inspect", lambda engine: FakeInspector())

    connector = DatabaseConnector(connection=BigQueryURL(project_id="project", dataset="dataset"))

    assert created["connection"] == "bigquery://project/dataset"
    assert connector.database_name == "project:dataset"
    assert connector.database_type == "BigQuery"
    assert isinstance(connector.inspector, FakeInspector)


def test_database_connector_passes_url_builder_engine_kwargs(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT_ID", raising=False)
    created = {}

    def fake_create_engine(connection, **kwargs):
        created["connection"] = connection
        created["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("piglets.database.database_connector.create_engine", fake_create_engine)
    monkeypatch.setattr("piglets.database.database_connector.inspect", lambda engine: FakeInspector())

    DatabaseConnector(
        connection=BigQueryURL(
            project_id="bigquery-public-data",
            dataset="stackoverflow",
            billing_project_id="billing-project",
        )
    )

    assert created["connection"] == "bigquery://bigquery-public-data/stackoverflow"
    assert created["kwargs"] == {"billing_project_id": "billing-project"}


def test_database_connector_uses_unhidden_url_builder_string(monkeypatch):
    created = {}

    def fake_create_engine(connection):
        created["connection"] = connection
        return object()

    monkeypatch.setattr("piglets.database.database_connector.create_engine", fake_create_engine)
    monkeypatch.setattr("piglets.database.database_connector.inspect", lambda engine: FakeInspector())

    DatabaseConnector(
        connection=SnowflakeURL(
            account="account",
            user="user",
            password="secret/password",
            database="database",
        )
    )

    assert "secret%2Fpassword" in created["connection"]


def test_database_connector_accepts_connection_string(monkeypatch):
    created = {}

    def fake_create_engine(connection):
        created["connection"] = connection
        return object()

    monkeypatch.setattr("piglets.database.database_connector.create_engine", fake_create_engine)
    monkeypatch.setattr("piglets.database.database_connector.inspect", lambda engine: FakeInspector())

    connector = DatabaseConnector(connection="duckdb:///analytics.db")

    assert created["connection"] == "duckdb:///analytics.db"
    assert connector.database_name == "analytics.db"
    assert connector.database_type == "DuckDB"


def test_database_connector_renders_sqlalchemy_url_object(monkeypatch):
    created = {}

    def fake_create_engine(connection):
        created["connection"] = connection
        return object()

    monkeypatch.setattr("piglets.database.database_connector.create_engine", fake_create_engine)
    monkeypatch.setattr("piglets.database.database_connector.inspect", lambda engine: FakeInspector())
    connection = URL.create(drivername="duckdb", database="analytics.db")

    connector = DatabaseConnector(connection=connection)

    assert created["connection"] == "duckdb:///analytics.db"
    assert connector.database_name == "analytics.db"
    assert connector.database_type == "DuckDB"


def test_database_connector_execute_query_accepts_string(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)

    result = connector.execute_query(
        "SELECT id, status FROM orders ORDER BY id"
    )

    assert isinstance(result, QueryResult)
    assert result.query == "SELECT id, status FROM orders ORDER BY id"
    assert result.columns == ["id", "status"]
    assert result.rows == [(1, "open"), (2, "closed")]
    assert result.row_count == 2


def test_database_connector_adds_schema_to_empty_search_space(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)

    search_space = connector.add_to_search_space(SearchSpace())

    assert isinstance(search_space, SearchSpace)
    assert search_space.database_schema is not None
    assert search_space.database_schema.name.endswith("orders.db")
    assert search_space.database_schema.database_type == "SQLite"
    assert [table.name for table in search_space.database_schema.table_schemas] == [
        "orders",
    ]


def test_database_connector_rejects_populated_search_space(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)
    search_space = connector.add_to_search_space(SearchSpace())

    with pytest.raises(ValueError, match="Multi-database search spaces"):
        connector.add_to_search_space(search_space)


def test_database_connector_execute_query_accepts_sql_query(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)

    result = connector.execute_query(
        SQLQuery(query="SELECT status FROM orders WHERE id = 1")
    )

    assert result.columns == ["status"]
    assert result.rows == [("open",)]
    assert result.row_count == 1


def test_database_connector_execute_query_accepts_profiling_query(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)

    result = connector.execute_query(
        ProfilingQuery(
            motivation="Check status values.",
            query="SELECT DISTINCT status FROM orders ORDER BY status",
        )
    )

    assert result.columns == ["status"]
    assert result.rows == [("closed",), ("open",)]
    assert result.row_count == 2


def test_database_connector_execute_query_rejects_empty_query(tmp_path):
    connector = _sqlite_connector_with_orders(tmp_path)

    with pytest.raises(ValueError, match="query must not be empty"):
        connector.execute_query("  ")


def _sqlite_connector_with_orders(tmp_path):
    db_path = tmp_path / "orders.db"
    connector = DatabaseConnector(
        connection=URL.create(drivername="sqlite", database=str(db_path))
    )

    with connector.engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT)")
        )
        connection.execute(
            text("INSERT INTO orders (id, status) VALUES (1, 'open'), (2, 'closed')")
        )

    return connector
