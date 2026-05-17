import pytest
from pydantic import ValidationError

from piglets.types import Column, Database, Table


def test_table_columns_to_string_formats_columns_with_description_placeholder():
    table = Table(
        name="users",
        columns=[
            Column(name="id", data_type="INTEGER"),
            Column(name="email", data_type="VARCHAR"),
        ],
    )

    assert table.columns_to_string() == "id (INTEGER):\nemail (VARCHAR):"


def test_database_requires_database_type():
    with pytest.raises(ValidationError):
        Database(name="example", tables=[])


def test_database_subtract_removes_matching_tables_and_columns():
    source_database = Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="VARCHAR"),
                    Column(name="email", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="orders",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="user_id", data_type="INTEGER"),
                    Column(name="total", data_type="NUMERIC"),
                ],
            ),
            Table(
                name="audit_log",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )
    database_to_subtract = Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="email", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="orders",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="user_id", data_type="INTEGER"),
                    Column(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )

    remaining_database = source_database.subtract(database_to_subtract)

    assert remaining_database.database_type == "DuckDB"
    assert remaining_database == Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="audit_log",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )


def test_database_union_combines_tables_and_columns_without_duplicates():
    left_database = Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="audit_log",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="event", data_type="VARCHAR"),
                ],
            ),
        ],
    )
    right_database = Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="email", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="orders",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )

    union_database = left_database.union(right_database)

    assert union_database.database_type == "DuckDB"
    assert union_database == Database(
        name="example",
        database_type="DuckDB",
        tables=[
            Table(
                name="users",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="VARCHAR"),
                    Column(name="email", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="audit_log",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="event", data_type="VARCHAR"),
                ],
            ),
            Table(
                name="orders",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="total", data_type="NUMERIC"),
                ],
            ),
        ],
    )
