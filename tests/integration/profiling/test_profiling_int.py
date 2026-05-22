import pytest
import re

from piglets import (
    DatabaseSchema,
    DatabaseProfileResult,
    ParallelDataProfiler,
    ProfilingQueries,
    ProfilingQuery,
    QueryResult,
    QueryResults,
    SearchSpace,
    TableSchema,
    TableProfileResult,
)

@pytest.fixture
def profiler(model_name, pruned_duckdb_search_space) -> ParallelDataProfiler:
    return ParallelDataProfiler(model_name=model_name, search_space=pruned_duckdb_search_space)

@pytest.fixture
def table(pruned_duckdb_search_space) -> TableSchema:
    assert pruned_duckdb_search_space.database_schema is not None
    return pruned_duckdb_search_space.database_schema.table_schemas[0]

def test_generate_table_profiler_queries(
    profiler,
    question,
    table,
    semantic_linking_result,
):

    profiling_queries = profiler._generate_table_profiler_queries(
        question=question,
        table_schema=table,
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
    question,
    table,
    semantic_linking_result,
    duckdb_connector,
):
    profiling_queries = ProfilingQueries(
        query=[
            ProfilingQuery(
                motivation="Count rows in the target table.",
                query=f"SELECT COUNT(*) AS row_count FROM {table.name}",
            ),
            ProfilingQuery(
                motivation="Check distinct orders represented by line items.",
                query=(
                    f"SELECT COUNT(DISTINCT l_orderkey) AS distinct_orders "
                    f"FROM {table.name}"
                ),
            ),
            ProfilingQuery(
                motivation="Inspect shipment date coverage.",
                query=(
                    "SELECT MIN(l_shipdate) AS min_shipdate, "
                    "MAX(l_shipdate) AS max_shipdate "
                    f"FROM {table.name}"
                ),
            ),
        ]
    )

    query_results: QueryResults = profiler._execute_table_profiling_queries(
        database_connector=duckdb_connector,
        profiling_queries=profiling_queries,
        question=question,
        table_schema=table,
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
        question,
        table,
        duckdb_connector,
        semantic_linking_result
):
    table_profile_result: TableProfileResult = profiler.profile_table(
        question=question,
        table_schema=table,
        database_connector=duckdb_connector,
        semantic_linking_result=semantic_linking_result
    )

    print(f"Relevant: {table_profile_result.relevant}")
    print(f"TableSchema summary: {table_profile_result.table_summary}")
    print("Relevant columns:")
    for column_result in table_profile_result.relevant_columns:
        print(f"- {column_result.column_name}: {column_result.relevance_reason}")

    assert isinstance(table_profile_result, TableProfileResult)
    assert isinstance(table_profile_result.relevant, bool)
    assert table_profile_result.table_summary.strip()
    assert isinstance(table_profile_result.relevant_columns, list)

    table_column_names = {column.name for column in table.column_schemas}
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
    question,
    pruned_duckdb_search_space,
    table,
    duckdb_connector,
    semantic_linking_result,
):
    assert pruned_duckdb_search_space.database_schema is not None
    single_table_database = DatabaseSchema(
        name=pruned_duckdb_search_space.database_schema.name,
        database_type=pruned_duckdb_search_space.database_schema.database_type,
        table_schemas=[table],
    )

    database_profile_result: DatabaseProfileResult = profiler.profile_database(
        search_space=SearchSpace(database_schema=single_table_database),
        database_connector=duckdb_connector,
        question=question,
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
    assert len(database_profile_result.table_profile_results) == len(single_table_database.table_schemas)

    table_column_names = {column.name for column in table.column_schemas}
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
