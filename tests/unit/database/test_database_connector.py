from sqlalchemy.engine import URL

from piglets.database.database_connector import (
    DatabaseConnector,
    database_name_from_connection,
    database_name_from_connection_string,
)
from piglets.database.url import BigQueryURL, DuckDBURL, MotherDuckURL, SnowflakeURL


class FakeInspector:
    pass


def test_database_name_from_bigquery_connection(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT_ID", raising=False)

    assert database_name_from_connection(
        BigQueryURL(project_id="project", dataset="dataset")
    ) == "project:dataset"
    assert database_name_from_connection(BigQueryURL(project_id="project")) == "project"
    assert database_name_from_connection(BigQueryURL(dataset="dataset")) == "dataset"
    assert database_name_from_connection(BigQueryURL()) == "bigquery"


def test_database_name_from_bigquery_connection_uses_env_project(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT_ID", "env-project")

    assert database_name_from_connection(BigQueryURL(dataset="dataset")) == "env-project:dataset"
    assert database_name_from_connection(BigQueryURL()) == "env-project"


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


def test_database_connector_accepts_url_builder(monkeypatch):
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
    assert isinstance(connector.inspector, FakeInspector)


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
