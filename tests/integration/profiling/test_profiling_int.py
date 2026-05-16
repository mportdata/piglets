import re

from piglets import Profiler, ProfilingQueries, Table

def test_table_profiling(
    model_name,
    natural_language_query,
    pruned_duckdb_database,
    semantic_linking_result,
):
    database_type = "duckdb"
    table: Table = pruned_duckdb_database.tables[0]

    profiler = Profiler(model_name=model_name)

    profiling_queries = profiler.profile_table(
        natural_language_query=natural_language_query,
        database_type=database_type,
        table=table,
        semantic_linking_result=semantic_linking_result
    )

    assert isinstance(profiling_queries, ProfilingQueries)
    assert 3 <= len(profiling_queries.exploratory_queries) <= 8

    for profiling_query in profiling_queries.exploratory_queries:
        query = profiling_query.query.strip()

        print(f"Motivation: {profiling_query.motivation}")
        print(f"Query: {query}")
        print("-" * 50)

        assert profiling_query.motivation.strip()
        assert query
        assert "```" not in query
        assert "-- motivation" not in query.lower()
        assert not re.search(r"\bjoin\b", query, re.IGNORECASE)
