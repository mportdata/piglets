import os

import pytest

from piglets.types import Database, Column, Table

pytest.importorskip("sqlalchemy_bigquery")

from piglets.database import BigQueryURL, DatabaseConnector, SnowflakeURL

@pytest.fixture
def biquery_connector():
    database_connector = DatabaseConnector(
        connection=BigQueryURL(dataset="stack_overflow"),
    )
    return database_connector

@pytest.fixture
def snowflake_connector():
    database_connector = DatabaseConnector(
        connection=SnowflakeURL(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="SNOWFLAKE_SAMPLE_DATA",
            schema="TPCH_SF1",
        ),
    )
    return database_connector

def test_bigquery_connector_get_database_schema(biquery_connector):
    database_schema: Database = biquery_connector.get_database_schema()

    assert isinstance(database_schema, Database)
    assert database_schema.name == "stack_overflow"
    assert len(database_schema.tables) > 0
    assert all(isinstance(table, Table) for table in database_schema.tables)
    for table in database_schema.tables:
        assert len(table.columns) > 0
        assert all(isinstance(column, Column) for column in table.columns)
        assert all(isinstance(column.name, str) for column in table.columns)
        assert all(isinstance(column.data_type, str) for column in table.columns)

def test_bigquery_connector_export_database_as_string(biquery_connector):
    database_schema: Database = biquery_connector.get_database_schema()
    database_string = database_schema.export_as_string()
    assert isinstance(database_string, str)
    assert "Database: stack_overflow" in database_string

def test_snowflake_connector_get_database_schema(snowflake_connector):
    database_schema: Database = snowflake_connector.get_database_schema()

    assert isinstance(database_schema, Database)
    assert database_schema.name == "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1"
    assert len(database_schema.tables) > 0
    assert all(isinstance(table, Table) for table in database_schema.tables)
    for table in database_schema.tables:
        assert len(table.columns) > 0
        assert all(isinstance(column, Column) for column in table.columns)
        assert all(isinstance(column.name, str) for column in table.columns)
        assert all(isinstance(column.data_type, str) for column in table.columns)
