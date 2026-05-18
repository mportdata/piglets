import pytest
import re

from piglets import (
    Database,
    DatabaseProfileResult,
    Profiler,
    ProfilingQueries,
    QueryResult,
    QueryResults,
    Table,
    TableProfileResult,
)

@pytest.fixture
def profiler(model_name, pruned_duckdb_database) -> Profiler:
    return Profiler(model_name=model_name, database=pruned_duckdb_database)

@pytest.fixture
def table(pruned_duckdb_database) -> Table:
    return pruned_duckdb_database.tables[0]

def test_generate_table_profiler_queries(
    profiler,
    natural_language_query,
    table,
    semantic_linking_result,
):

    profiling_queries = profiler._generate_table_profiler_queries(
        natural_language_query=natural_language_query,
        table=table,
        semantic_linking_result=semantic_linking_result
    )

    assert isinstance(profiling_queries, ProfilingQueries)
    assert 3 <= len(profiling_queries.query) <= 8

    for profiling_query in profiling_queries.query:
        query = profiling_query.query.strip()

        print(f"Motivation: {profiling_query.motivation}")
        print(f"Query: {query}")
        print("-" * 50)

        assert profiling_query.motivation.strip()
        assert query
        assert "```" not in query
        assert "-- motivation" not in query.lower()
        assert not re.search(r"\bjoin\b", query, re.IGNORECASE)

def test_executetable_profiling_queries(
    profiler,
    natural_language_query,
    table,
    semantic_linking_result,
    duckdb_connector,
):
    profiling_queries = profiler._generate_table_profiler_queries(
        natural_language_query=natural_language_query,
        table=table,
        semantic_linking_result=semantic_linking_result
    )

    query_results: QueryResults = profiler._execute_table_profiling_queries(
        database_connector=duckdb_connector,
        profiling_queries=profiling_queries,
    )

    assert isinstance(query_results, QueryResults)
    assert len(query_results.query_results) == len(profiling_queries.query)
    assert 3 <= len(query_results.query_results) <= 8

    for profiling_query, query_result in zip(
        profiling_queries.query,
        query_results.query_results,
    ):
        query = query_result.query.strip()

        assert isinstance(query_result, QueryResult)
        assert query_result.query == profiling_query.query
        assert query
        assert query_result.columns
        assert query_result.row_count == len(query_result.rows)

        for row in query_result.rows:
            assert isinstance(row, tuple)
            assert len(row) == len(query_result.columns)

        assert "```" not in query
        assert "-- motivation" not in query.lower()
        assert not re.search(r"\bjoin\b", query, re.IGNORECASE)

    query_results_string: str = query_results.to_string()

    assert isinstance(query_results_string, str)
    assert query_results_string.strip()
    assert f"Query Results: {len(query_results.query_results)}" in query_results_string

    for index, query_result in enumerate(query_results.query_results, start=1):
        assert (
            f"Query Result {index} of {len(query_results.query_results)}"
            in query_results_string
        )
        assert f"Query: {query_result.query}" in query_results_string
        assert f"Rows returned: {query_result.row_count}" in query_results_string

    assert "Rows shown:" in query_results_string

def test_profile_table(
        profiler,
        natural_language_query,
        table,
        duckdb_connector,
        semantic_linking_result
):
    table_profile_result: TableProfileResult = profiler.profile_table(
        natural_language_query=natural_language_query,
        table=table,
        database_connector=duckdb_connector,
        semantic_linking_result=semantic_linking_result
    )

    print(f"Relevant: {table_profile_result.relevant}")
    print(f"Table summary: {table_profile_result.table_summary}")
    print("Relevant columns:")
    for column_result in table_profile_result.relevant_columns:
        print(f"- {column_result.column_name}: {column_result.relevance_reason}")

    assert isinstance(table_profile_result, TableProfileResult)
    assert isinstance(table_profile_result.relevant, bool)
    assert table_profile_result.table_summary.strip()
    assert isinstance(table_profile_result.relevant_columns, list)

    table_column_names = {column.name for column in table.columns}
    seen_column_names = set()
    for column_result in table_profile_result.relevant_columns:
        assert column_result.column_name.strip()
        assert column_result.column_name in table_column_names
        assert column_result.column_name not in seen_column_names
        assert column_result.relevance_reason.strip()
        assert column_result.observations.strip()
        seen_column_names.add(column_result.column_name)

    if table_profile_result.relevant:
        assert table_profile_result.relevant_columns


def test_profile_database(
    profiler,
    natural_language_query,
    pruned_duckdb_database,
    table,
    duckdb_connector,
    semantic_linking_result,
):
    single_table_database = Database(
        name=pruned_duckdb_database.name,
        database_type=pruned_duckdb_database.database_type,
        tables=[table],
    )

    database_profile_result: DatabaseProfileResult = profiler.profile_database(
        database=single_table_database,
        database_connector=duckdb_connector,
        natural_language_query=natural_language_query,
        semantic_linking_result=semantic_linking_result,
    )

    print(f"Database: {database_profile_result.database_name}")
    print(f"Database type: {database_profile_result.database_type}")
    print(f"Table profiles: {len(database_profile_result.table_profile_results)}")
    for index, table_profile_result in enumerate(
        database_profile_result.table_profile_results,
        start=1,
    ):
        print(f"{index}. relevant={table_profile_result.relevant}")
        print(f"   summary={table_profile_result.table_summary}")
        print(f"   relevant columns={len(table_profile_result.relevant_columns)}")

    assert isinstance(database_profile_result, DatabaseProfileResult)
    assert database_profile_result.database_name == single_table_database.name
    assert database_profile_result.database_type == single_table_database.database_type
    assert len(database_profile_result.table_profile_results) == len(single_table_database.tables)

    table_column_names = {column.name for column in table.columns}
    for table_profile_result in database_profile_result.table_profile_results:
        assert isinstance(table_profile_result, TableProfileResult)
        assert isinstance(table_profile_result.relevant, bool)
        assert table_profile_result.table_summary.strip()
        assert isinstance(table_profile_result.relevant_columns, list)

        seen_column_names = set()
        for column_result in table_profile_result.relevant_columns:
            assert column_result.column_name.strip()
            assert column_result.column_name in table_column_names
            assert column_result.column_name not in seen_column_names
            assert column_result.relevance_reason.strip()
            assert column_result.observations.strip()
            seen_column_names.add(column_result.column_name)

        if table_profile_result.relevant:
            assert table_profile_result.relevant_columns
