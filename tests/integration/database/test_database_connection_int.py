import pytest

from piglets.types import Database, Column, Table

pytest.importorskip("sqlalchemy")
pytest.importorskip("sqlalchemy_bigquery")

from piglets.database import DatabaseConnector

@pytest.fixture
def biquery_connector():
    database_connector = DatabaseConnector(
        database_type="bigquery",
        database_name="stack_overflow",
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
