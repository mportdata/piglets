from piglets.types import Column, Database, Table


def test_database_subtract_removes_matching_tables_and_columns():
    source_database = Database(
        name="example",
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

    print(f"Source database: {source_database}")
    print(f"Database to subtract: {database_to_subtract}")
    print(f"Remaining database: {remaining_database}")

    assert remaining_database == Database(
        name="example",
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

    print(f"Left database: {left_database}")
    print(f"Right database: {right_database}")
    print(f"Union database: {union_database}")

    assert union_database == Database(
        name="example",
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
