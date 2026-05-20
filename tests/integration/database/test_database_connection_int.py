from piglets.types import DatabaseSchema, ColumnSchema, QueryResult, TableSchema


def test_duckdb_connector_get_database_schema(duckdb_database_schema):
    database_schema: DatabaseSchema = duckdb_database_schema

    assert isinstance(database_schema, DatabaseSchema)
    assert database_schema.name.endswith("tpch_sf001.duckdb")
    assert database_schema.database_type == "DuckDB"
    assert len(database_schema.table_schemas) > 0
    assert all(isinstance(table, TableSchema) for table in database_schema.table_schemas)
    for table in database_schema.table_schemas:
        assert len(table.column_schemas) > 0
        assert all(isinstance(column, ColumnSchema) for column in table.column_schemas)
        assert all(isinstance(column.name, str) for column in table.column_schemas)
        assert all(isinstance(column.data_type, str) for column in table.column_schemas)

def test_duckdb_connector_export_database_as_string(duckdb_database_schema):
    database_schema: DatabaseSchema = duckdb_database_schema
    database_string = database_schema.export_as_string()
    assert isinstance(database_string, str)
    assert "Database:" in database_string
    assert "Database Type: DuckDB" in database_string
    assert "customer" in database_string


def test_duckdb_connector_execute_query(duckdb_connector):
    query = "SELECT COUNT(*) AS customer_count FROM customer"

    result = duckdb_connector.execute_query(query)

    assert isinstance(result, QueryResult)
    assert result.query == query
    assert result.columns == ["customer_count"]
    assert result.row_count == 1
    assert len(result.rows) == 1
    assert result.rows[0][0] > 0
    result_string = result.to_string()
    assert "customer_count" in result_string
    assert "Rows returned: 1" in result_string


def test_duckdb_query_result_to_string(duckdb_connector):
    result = duckdb_connector.execute_query(
        """
        SELECT c_custkey, c_name
        FROM customer
        ORDER BY c_custkey
        LIMIT 3
        """
    )

    result_string = result.to_string(max_rows=2)

    assert "Rows returned: 3" in result_string
    assert "Rows shown: 2" in result_string
    assert "| c_custkey | c_name |" in result_string
    assert "| --- | --- |" in result_string
    assert "| 1 | Customer#000000001 |" in result_string
    assert "| 2 | Customer#000000002 |" in result_string
    assert "Customer#000000003" not in result_string
    assert "... truncated 1 rows" in result_string


def test_bigquery_connector_get_database_schema(bigquery_database_schema):
    database_schema: DatabaseSchema = bigquery_database_schema

    assert isinstance(database_schema, DatabaseSchema)
    assert database_schema.database_type == "BigQuery"
    assert len(database_schema.table_schemas) > 0
    assert all(isinstance(table, TableSchema) for table in database_schema.table_schemas)
    for table in database_schema.table_schemas:
        assert len(table.column_schemas) > 0
        assert all(isinstance(column, ColumnSchema) for column in table.column_schemas)
        assert all(isinstance(column.name, str) for column in table.column_schemas)
        assert all(isinstance(column.data_type, str) for column in table.column_schemas)


def test_snowflake_connector_get_database_schema(snowflake_connector):
    database_schema: DatabaseSchema = snowflake_connector.get_database_schema()

    assert isinstance(database_schema, DatabaseSchema)
    assert database_schema.name == "SNOWFLAKE_SAMPLE_DATA.TPCH_SF1"
    assert database_schema.database_type == "Snowflake"
    assert len(database_schema.table_schemas) > 0
    assert all(isinstance(table, TableSchema) for table in database_schema.table_schemas)
    for table in database_schema.table_schemas:
        assert len(table.column_schemas) > 0
        assert all(isinstance(column, ColumnSchema) for column in table.column_schemas)
        assert all(isinstance(column.name, str) for column in table.column_schemas)
        assert all(isinstance(column.data_type, str) for column in table.column_schemas)
