import pytest
from pydantic import ValidationError

from piglets.types import ColumnSchema, DatabaseSchema, TableSchema


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
