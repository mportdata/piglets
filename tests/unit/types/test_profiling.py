from piglets.types import (
    ColumnSchema,
    DatabaseSchema,
    DatabaseProfileResult,
    TableSchema,
    TableProfileColumnResult,
    TableProfileResult,
)


def test_table_profile_result_can_describe_relevant_columns():
    result = TableProfileResult(
        table_name="orders",
        relevant=True,
        relevant_columns=[
            TableProfileColumnResult(
                column_name="status",
                relevance_reason="Identifies cancelled orders.",
                observations="Values include cancelled and complete.",
            )
        ],
        table_summary="Order status table relevant to cancellation analysis.",
    )

    assert result.relevant is True
    assert result.table_name == "orders"
    assert len(result.relevant_columns) == 1
    assert result.relevant_columns[0].column_name == "status"
    assert result.table_summary


def test_table_profile_result_to_string_renders_schema_status_block():
    table = TableSchema(
        name="orders",
        column_schemas=[
            ColumnSchema(name="order_id", data_type="INTEGER"),
            ColumnSchema(name="status", data_type="VARCHAR"),
        ],
    )
    result = TableProfileResult(
        table_name="orders",
        relevant=True,
        relevant_columns=[
            TableProfileColumnResult(
                column_name="status",
                relevance_reason="Needed for filtering cancelled orders.",
                observations="Values include cancelled and complete.",
            )
        ],
        table_summary="Order table relevant to cancellation analysis.",
    )

    result_string = result.to_string(table)

    assert "Table: orders [MARKED RELEVANT]" in result_string
    assert "Columns:" in result_string
    assert "order_id (INTEGER):" in result_string
    assert "status (VARCHAR):" in result_string
    assert "Observations: Values include cancelled and complete." in result_string
    assert "Reason: Needed for filtering cancelled orders." in result_string
    assert "Observations: Order table relevant to cancellation analysis." in result_string
    assert "Reason: No column-level relevance reason identified." in result_string


def test_database_profile_result_to_string_matches_by_table_name_and_marks_unknown():
    database = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="order_id", data_type="INTEGER"),
                    ColumnSchema(name="status", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="customers",
                column_schemas=[
                    ColumnSchema(name="customer_id", data_type="INTEGER"),
                ],
            ),
            TableSchema(
                name="lineitem",
                column_schemas=[
                    ColumnSchema(name="order_id", data_type="INTEGER"),
                ],
            ),
        ],
    )
    profile_result = DatabaseProfileResult(
        database_name="example",
        database_type="DuckDB",
        table_profile_results=[
            TableProfileResult(
                table_name="lineitem",
                relevant=False,
                relevant_columns=[],
                table_summary="Lineitem is not needed for this question.",
            ),
            TableProfileResult(
                table_name="orders",
                relevant=True,
                relevant_columns=[
                    TableProfileColumnResult(
                        column_name="status",
                        relevance_reason="Needed for filtering cancelled orders.",
                        observations="Values include cancelled and complete.",
                    )
                ],
                table_summary="Order table relevant to cancellation analysis.",
            ),
        ],
    )

    result_string = profile_result.to_string(database)

    assert "Database Profile: example" in result_string
    assert "Database Type: DuckDB" in result_string
    assert "Table Profiles: 2" in result_string
    assert result_string.index("Table: orders [MARKED RELEVANT]") < result_string.index(
        "Table: customers [MARKED UNKNOWN]"
    )
    assert result_string.index("Table: customers [MARKED UNKNOWN]") < result_string.index(
        "Table: lineitem [MARKED IRRELEVANT]"
    )
    assert "customer_id (INTEGER):" in result_string
    assert "Observations: No empirical profile evidence available for this table." in result_string
    assert "Reason: No profiling decision available." in result_string
