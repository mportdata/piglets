import pytest
from pydantic import ValidationError

from piglets.types import (
    ColumnSchema,
    DatabaseSchema,
    DatabaseSemanticAnnotation,
    TableSchema,
    TableSemanticAnnotation,
)


def test_table_columns_to_string_formats_columns_with_description_placeholder():
    table = TableSchema(
        name="users",
        column_schemas=[
            ColumnSchema(name="id", data_type="INTEGER"),
            ColumnSchema(name="email", data_type="VARCHAR"),
        ],
    )

    assert table.columns_to_string() == "id (INTEGER):\nemail (VARCHAR):"


def test_database_requires_database_type():
    with pytest.raises(ValidationError):
        DatabaseSchema(name="example", table_schemas=[])


def test_schema_semantic_annotations_default_to_none():
    database_schema = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                ],
            )
        ],
    )

    assert database_schema.semantic_annotation is None
    assert database_schema.table_schemas[0].semantic_annotation is None


def test_schema_semantic_annotations_can_be_set():
    database_schema = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        semantic_annotation=DatabaseSemanticAnnotation(
            database_structure="Customer database.",
            query_specific_content_analysis="Users table answers the question.",
        ),
        table_schemas=[
            TableSchema(
                name="users",
                semantic_annotation=TableSemanticAnnotation(
                    function="Target table."
                ),
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                ],
            )
        ],
    )

    assert database_schema.semantic_annotation is not None
    assert database_schema.semantic_annotation.database_structure == "Customer database."
    assert database_schema.table_schemas[0].semantic_annotation is not None
    assert database_schema.table_schemas[0].semantic_annotation.function == "Target table."


def test_database_subtract_removes_matching_tables_and_columns():
    source_database = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                    ColumnSchema(name="email", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="user_id", data_type="INTEGER"),
                    ColumnSchema(name="total", data_type="NUMERIC"),
                ],
            ),
            TableSchema(
                name="audit_log",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )
    database_to_subtract = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="email", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="user_id", data_type="INTEGER"),
                    ColumnSchema(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )

    remaining_database = source_database.subtract(database_to_subtract)

    assert remaining_database.database_type == "DuckDB"
    assert remaining_database == DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="audit_log",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )


def test_database_union_combines_tables_and_columns_without_duplicates():
    left_database = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="audit_log",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )
    right_database = DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="email", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )

    union_database = left_database.union(right_database)

    assert union_database.database_type == "DuckDB"
    assert union_database == DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="users",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                    ColumnSchema(name="email", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="audit_log",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="event", data_type="VARCHAR"),
                ],
            ),
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="id", data_type="INTEGER"),
                    ColumnSchema(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )
