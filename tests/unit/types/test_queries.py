import pytest

from piglets import QueryResult as RootQueryResult
from piglets import QueryResults as RootQueryResults
from piglets.types import QueryResult, QueryResults


def test_query_result_is_exported_from_root_package():
    assert RootQueryResult is QueryResult
    assert RootQueryResults is QueryResults


def test_query_result_rows_as_dicts_uses_column_order():
    result = QueryResult(
        query="SELECT id, name FROM users",
        columns=["id", "name"],
        rows=[(1, "Ada"), (2, "Grace")],
        row_count=2,
    )

    assert result.rows_as_dicts() == [
        {"id": 1, "name": "Ada"},
        {"id": 2, "name": "Grace"},
    ]


def test_query_result_to_string_renders_table_preview():
    result = QueryResult(
        query="SELECT id, name FROM users",
        columns=["id", "name"],
        rows=[(1, "Ada"), (2, "Grace"), (3, "Katherine")],
        row_count=3,
    )

    result_string = result.to_string(max_rows=2)

    assert "Query: SELECT id, name FROM users" in result_string
    assert "Rows returned: 3" in result_string
    assert "Rows shown: 2" in result_string
    assert "| id | name |" in result_string
    assert "| 1 | Ada |" in result_string
    assert "| 2 | Grace |" in result_string
    assert "Katherine" not in result_string
    assert "... truncated 1 rows" in result_string


def test_query_result_to_string_truncates_cells_and_escapes_table_values():
    result = QueryResult(
        query="SELECT note FROM notes",
        columns=["note"],
        rows=[("alpha|beta\ngamma",)],
        row_count=1,
    )

    result_string = result.to_string(max_cell_length=12)

    assert "alpha\\|be..." in result_string
    assert "\ngamma" not in result_string


def test_query_result_to_string_handles_zero_rows():
    result = QueryResult(
        query="SELECT id FROM users WHERE 1 = 0",
        columns=["id"],
        rows=[],
        row_count=0,
    )

    result_string = result.to_string()

    assert "Rows returned: 0" in result_string
    assert "Rows shown: 0" in result_string
    assert "| id |" in result_string


def test_query_result_to_string_rejects_invalid_limits():
    result = QueryResult(query="SELECT 1")

    with pytest.raises(ValueError, match="max_rows"):
        result.to_string(max_rows=-1)

    with pytest.raises(ValueError, match="max_cell_length"):
        result.to_string(max_cell_length=0)


def test_query_results_to_string_handles_empty_results():
    results = QueryResults()

    assert results.to_string() == "Query Results: 0"


def test_query_results_to_string_renders_numbered_result_blocks():
    results = QueryResults(
        query_results=[
            QueryResult(
                query="SELECT id FROM users",
                columns=["id"],
                rows=[(1,), (2,)],
                row_count=2,
            ),
            QueryResult(
                query="SELECT COUNT(*) AS user_count FROM users",
                columns=["user_count"],
                rows=[(2,)],
                row_count=1,
            ),
        ]
    )

    results_string = results.to_string()

    assert "Query Results: 2" in results_string
    assert "Query Result 1 of 2" in results_string
    assert "Query: SELECT id FROM users" in results_string
    assert "| id |" in results_string
    assert "| 1 |" in results_string
    assert "Query Result 2 of 2" in results_string
    assert "Query: SELECT COUNT(*) AS user_count FROM users" in results_string
    assert "| user_count |" in results_string
    assert "| 2 |" in results_string


def test_query_results_to_string_passes_rendering_limits_to_results():
    results = QueryResults(
        query_results=[
            QueryResult(
                query="SELECT note FROM notes",
                columns=["note"],
                rows=[
                    ("alpha|beta\ngamma",),
                    ("second row should be hidden",),
                ],
                row_count=2,
            )
        ]
    )

    results_string = results.to_string(max_rows=1, max_cell_length=12)

    assert "Rows shown: 1" in results_string
    assert "alpha\\|be..." in results_string
    assert "second row should be hidden" not in results_string
    assert "... truncated 1 rows" in results_string
