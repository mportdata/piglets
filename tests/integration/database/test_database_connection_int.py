from piglets.types import Database, Column, Table


def test_duckdb_connector_get_database_schema(duckdb_database):
    database_schema: Database = duckdb_database

    assert isinstance(database_schema, Database)
    assert database_schema.name.endswith("tpch_sf001.duckdb")
    assert len(database_schema.tables) > 0
    assert all(isinstance(table, Table) for table in database_schema.tables)
    for table in database_schema.tables:
        assert len(table.columns) > 0
        assert all(isinstance(column, Column) for column in table.columns)
        assert all(isinstance(column.name, str) for column in table.columns)
        assert all(isinstance(column.data_type, str) for column in table.columns)

def test_duckdb_connector_export_database_as_string(duckdb_database):
    database_schema: Database = duckdb_database
    database_string = database_schema.export_as_string()
    assert isinstance(database_string, str)
    assert "Database:" in database_string
    assert "customer" in database_string


def test_bigquery_connector_get_database_schema(bigquery_database):
    database_schema: Database = bigquery_database

    assert isinstance(database_schema, Database)
    assert len(database_schema.tables) > 0
    assert all(isinstance(table, Table) for table in database_schema.tables)
    for table in database_schema.tables:
        assert len(table.columns) > 0
        assert all(isinstance(column, Column) for column in table.columns)
        assert all(isinstance(column.name, str) for column in table.columns)
        assert all(isinstance(column.data_type, str) for column in table.columns)


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
