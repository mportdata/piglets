import logging
import threading
import time

import pytest

from piglets.policies import SemanticRules
from piglets.profiling.profiler import Profiler
from piglets.types import (
    ColumnSchema,
    DatabaseSchema,
    ProfilingQueries,
    ProfilingQuery,
    Question,
    QueryResult,
    QueryResults,
    SearchSpace,
    SemanticLinkingResult,
    TableSchema,
    TableProfileColumnResult,
    TableProfileResult,
)


def _question() -> Question:
    return Question(natural_language_question="Which orders are cancelled?")


class FakeProfilingLLM:
    def __init__(self):
        self.prompts = []
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.schema is TableProfileResult:
            return TableProfileResult(
                table_name="llm_table_name",
                relevant=True,
                relevant_columns=[
                    TableProfileColumnResult(
                        column_name="status",
                        relevance_reason="Identifies cancelled orders.",
                        observations="Values include cancelled.",
                    )
                ],
                table_summary="Order table relevant to cancellation analysis.",
            )
        if self.schema is ProfilingQuery:
            return ProfilingQuery(
                motivation="Repair status values.",
                query="SELECT status FROM orders LIMIT 10",
            )
        return ProfilingQueries(
            query=[
                ProfilingQuery(
                    motivation="Check status values.",
                    query="SELECT DISTINCT status FROM orders LIMIT 10",
                )
            ]
        )


class FakeRepairConnector:
    def __init__(self, failures_by_query):
        self.failures_by_query = {
            query: list(errors)
            for query, errors in failures_by_query.items()
        }
        self.queries = []

    def execute_query(self, query):
        self.queries.append(query.query)
        errors = self.failures_by_query.get(query.query, [])
        if errors:
            raise errors.pop(0)

        return QueryResult(
            query=query.query,
            columns=["value"],
            rows=[(query.query,)],
            row_count=1,
        )


class FakeParallelConnector:
    def __init__(self):
        self.barrier = threading.Barrier(2)

    def execute_query(self, query):
        self.barrier.wait(timeout=1)
        if query.query == "SELECT 1":
            time.sleep(0.05)

        return QueryResult(
            query=query.query,
            columns=["value"],
            rows=[(query.query,)],
            row_count=1,
        )


class FakeParallelProfiler(Profiler):
    def __init__(self, database_schema):
        super().__init__(
            model_name="test-model",
            search_space=SearchSpace(database_schema=database_schema),
        )
        self.barrier = threading.Barrier(2)

    def profile_table(
        self,
        question,
        table_schema,
        database_connector,
        semantic_linking_result=None,
    ):
        self.barrier.wait(timeout=1)
        if table_schema.name == "orders":
            time.sleep(0.05)

        return TableProfileResult(
            table_name=table_schema.name,
            relevant=True,
            relevant_columns=[
                TableProfileColumnResult(
                    column_name=table_schema.column_schemas[0].name,
                    relevance_reason=f"{table_schema.name} is relevant.",
                    observations=f"{table_schema.name} was profiled.",
                )
            ],
            table_summary=f"{table_schema.name} summary.",
        )


def _table() -> TableSchema:
    return TableSchema(
        name="orders",
        column_schemas=[
            ColumnSchema(name="order_id", data_type="INTEGER"),
            ColumnSchema(name="status", data_type="VARCHAR"),
            ColumnSchema(name="created_at", data_type="TIMESTAMP"),
        ],
    )


def _database(table: TableSchema | None = None) -> DatabaseSchema:
    return DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[table or _table()],
    )


def _search_space(table: TableSchema | None = None) -> SearchSpace:
    return SearchSpace(database_schema=_database(table))


def _two_table_database() -> DatabaseSchema:
    return DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            _table(),
            TableSchema(
                name="customers",
                column_schemas=[
                    ColumnSchema(name="customer_id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                ],
            ),
        ],
    )


def _semantic_linking_result(table_name: str = "orders") -> SemanticLinkingResult:
    return SemanticLinkingResult(
        database_structure="Order database.",
        query_specific_content_analysis="Question maps to order status.",
        table_functions={
            table_name: "Contains order-level facts and status fields.",
        },
    )


def test_generate_table_profiler_queries_uses_structured_output_and_returns_profiling_queries(monkeypatch):
    fake_llm = FakeProfilingLLM()
    init_calls = []

    def fake_init_chat_model(model, model_provider=None):
        init_calls.append((model, model_provider))
        return fake_llm

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        fake_init_chat_model,
    )

    profiler = Profiler(
        model_name="test-model",
        search_space=_search_space(),
        model_provider="test-provider",
    )
    profiling_queries = profiler._generate_table_profiler_queries(
        question=_question(),
        table_schema=_table(),
        semantic_linking_result=_semantic_linking_result(),
    )

    assert init_calls == [("test-model", "test-provider")]
    assert fake_llm.schema is ProfilingQueries
    assert isinstance(profiling_queries, ProfilingQueries)
    assert len(profiling_queries.query) == 1
    assert profiling_queries.query[0].motivation
    assert profiling_queries.query[0].query


def test_generate_table_profiler_queries_prompt_uses_critical_rules_and_single_table_guidance(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(
        model_name="test-model",
        search_space=_search_space(),
        rules=SemanticRules(),
    )
    profiler._generate_table_profiler_queries(
        question=_question(),
        table_schema=_table(),
        semantic_linking_result=_semantic_linking_result(),
    )

    prompt = fake_llm.prompts[0]

    assert "*** TARGET TABLE: orders ***" in prompt
    assert "order_id (INTEGER):" in prompt
    assert "status (VARCHAR):" in prompt
    assert "created_at (TIMESTAMP):" in prompt
    assert "Use only tables, columns, and relationships" in prompt
    assert "Prefer explicit primary-key and foreign-key relationships" not in prompt
    assert "Each query must profile only the target table, orders." in prompt
    assert "Do not join to, reference, or infer data from any other table." in prompt
    assert "Generate 3-8 DUCKDB SQL queries to investigate." in prompt
    assert "query" in prompt
    assert "motivation" in prompt


def test_generate_table_profiler_queries_prompt_uses_case_insensitive_table_function_lookup(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    table = TableSchema(
        name="Orders",
        column_schemas=[
            ColumnSchema(name="status", data_type="VARCHAR"),
        ],
    )
    profiler = Profiler(model_name="test-model", search_space=_search_space(table))
    profiler._generate_table_profiler_queries(
        question=_question(),
        table_schema=table,
        semantic_linking_result=_semantic_linking_result(table_name="orders"),
    )

    assert "Contains order-level facts and status fields." in fake_llm.prompts[0]


def test_generate_table_profiler_queries_uses_unknown_role_without_semantic_linking(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(model_name="test-model", search_space=_search_space())
    profiling_queries = profiler._generate_table_profiler_queries(
        question=_question(),
        table_schema=_table(),
    )

    prompt = fake_llm.prompts[0]

    assert isinstance(profiling_queries, ProfilingQueries)
    assert "*** ANTICIPATED ROLE ***" in prompt
    assert "This table was identified as: Unknown Role." in prompt


def test_profile_table_can_be_called_without_semantic_linking(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(model_name="test-model", search_space=_search_space())
    profiling_queries = profiler._generate_table_profiler_queries(
        question=_question(),
        table_schema=_table(),
    )

    assert isinstance(profiling_queries, ProfilingQueries)
    assert "This table was identified as: Unknown Role." in fake_llm.prompts[0]


def test_profile_table_from_query_results_uses_structured_output_and_evidence(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(model_name="test-model", search_space=_search_space())
    query_results = QueryResults(
        query_results=[
            QueryResult(
                query="SELECT DISTINCT status FROM orders LIMIT 10",
                columns=["status"],
                rows=[("cancelled",), ("complete",)],
                row_count=2,
            )
        ]
    )

    table_profile_result = profiler._profile_table_from_query_results(
        question=_question(),
        query_results=query_results,
        table_schema=_table(),
    )

    prompt = fake_llm.prompts[0]

    assert fake_llm.schema is TableProfileResult
    assert isinstance(table_profile_result, TableProfileResult)
    assert table_profile_result.table_name == "orders"
    assert table_profile_result.relevant is True
    assert table_profile_result.relevant_columns
    assert "*** EXPLORATION EVIDENCE ***" in prompt
    assert query_results.to_string() in prompt
    assert "Which orders are cancelled?" in prompt
    assert "orders" in prompt


def test_execute_table_profiling_queries_runs_queries_in_parallel_and_preserves_order(caplog):
    caplog.set_level(logging.DEBUG, logger="piglets.profiling.profiler")
    profiler = Profiler(model_name="test-model", search_space=_search_space())
    profiling_queries = ProfilingQueries(
        query=[
            ProfilingQuery(motivation="First query.", query="SELECT 1"),
            ProfilingQuery(motivation="Second query.", query="SELECT 2"),
        ]
    )

    query_results = profiler._execute_table_profiling_queries(
        database_connector=FakeParallelConnector(),
        profiling_queries=profiling_queries,
        question=_question(),
        table_schema=_table(),
    )

    assert isinstance(query_results, QueryResults)
    assert [result.query for result in query_results.query_results] == [
        "SELECT 1",
        "SELECT 2",
    ]
    assert [result.rows for result in query_results.query_results] == [
        [("SELECT 1",)],
        [("SELECT 2",)],
    ]
    assert "Executing 2 profiling queries with 2 workers" in caplog.text
    assert "Executed 2 profiling queries" in caplog.text
    assert "SELECT 1" not in caplog.text
    assert "SELECT 2" not in caplog.text


def test_execute_table_profiling_queries_repairs_failed_query_and_preserves_order(monkeypatch):
    fake_llm = FakeProfilingLLM()
    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )
    profiler = Profiler(model_name="test-model", search_space=_search_space())
    connector = FakeRepairConnector(
        failures_by_query={
            "SELECT broken": [ValueError("Binder Error: invalid column")],
        }
    )
    profiling_queries = ProfilingQueries(
        query=[
            ProfilingQuery(motivation="First query.", query="SELECT 1"),
            ProfilingQuery(motivation="Broken query.", query="SELECT broken"),
            ProfilingQuery(motivation="Third query.", query="SELECT 3"),
        ]
    )

    query_results = profiler._execute_table_profiling_queries(
        database_connector=connector,
        profiling_queries=profiling_queries,
        question=_question(),
        table_schema=_table(),
    )

    assert [result.query for result in query_results.query_results] == [
        "SELECT 1",
        "SELECT status FROM orders LIMIT 10",
        "SELECT 3",
    ]
    assert sorted(connector.queries[:3]) == [
        "SELECT 1",
        "SELECT 3",
        "SELECT broken",
    ]
    assert connector.queries[3:] == ["SELECT status FROM orders LIMIT 10"]
    assert fake_llm.schema is ProfilingQuery


def test_repair_profiling_query_prompt_contains_failed_query_context(monkeypatch):
    fake_llm = FakeProfilingLLM()
    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )
    profiler = Profiler(model_name="test-model", search_space=_search_space())
    connector = FakeRepairConnector(
        failures_by_query={
            "SELECT broken": [ValueError("Binder Error: invalid column")],
        }
    )

    profiler._execute_table_profiling_queries(
        database_connector=connector,
        profiling_queries=ProfilingQueries(
            query=[
                ProfilingQuery(
                    motivation="Inspect order status.",
                    query="SELECT broken",
                )
            ]
        ),
        question=_question(),
        table_schema=_table(),
    )

    prompt = fake_llm.prompts[0]

    assert "*** SQL DIALECT ***" in prompt
    assert "DUCKDB SQL" in prompt
    assert "*** TARGET TABLE: orders ***" in prompt
    assert "order_id (INTEGER):" in prompt
    assert "status (VARCHAR):" in prompt
    assert "Which orders are cancelled?" in prompt
    assert "Inspect order status." in prompt
    assert "SELECT broken" in prompt
    assert "Binder Error: invalid column" in prompt
    assert "The query must profile only the target table, orders." in prompt


def test_execute_table_profiling_queries_raises_after_repair_attempts_exhausted(monkeypatch):
    fake_llm = FakeProfilingLLM()
    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )
    profiler = Profiler(
        model_name="test-model",
        search_space=_search_space(),
        max_query_repair_attempts=1,
    )
    connector = FakeRepairConnector(
        failures_by_query={
            "SELECT broken": [ValueError("Binder Error: invalid column")],
            "SELECT status FROM orders LIMIT 10": [
                ValueError("Binder Error: still invalid"),
            ],
        }
    )

    with pytest.raises(ValueError, match="still invalid"):
        profiler._execute_table_profiling_queries(
            database_connector=connector,
            profiling_queries=ProfilingQueries(
                query=[
                    ProfilingQuery(
                        motivation="Inspect order status.",
                        query="SELECT broken",
                    )
                ]
            ),
            question=_question(),
            table_schema=_table(),
        )

    assert connector.queries == [
        "SELECT broken",
        "SELECT status FROM orders LIMIT 10",
    ]


def test_execute_table_profiling_queries_does_not_repair_when_disabled(monkeypatch):
    init_calls = []

    def fake_init_chat_model(model, model_provider=None):
        init_calls.append((model, model_provider))
        return FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        fake_init_chat_model,
    )
    profiler = Profiler(
        model_name="test-model",
        search_space=_search_space(),
        max_query_repair_attempts=0,
    )
    connector = FakeRepairConnector(
        failures_by_query={
            "SELECT broken": [ValueError("Binder Error: invalid column")],
        }
    )

    with pytest.raises(ValueError, match="invalid column"):
        profiler._execute_table_profiling_queries(
            database_connector=connector,
            profiling_queries=ProfilingQueries(
                query=[
                    ProfilingQuery(
                        motivation="Inspect order status.",
                        query="SELECT broken",
                    )
                ]
            ),
            question=_question(),
            table_schema=_table(),
        )

    assert init_calls == []


def test_profile_database_profiles_tables_in_parallel_and_preserves_order(caplog):
    caplog.set_level(logging.DEBUG, logger="piglets.profiling.profiler")
    database = _two_table_database()
    profiler = FakeParallelProfiler(database)

    database_profile_result = profiler.profile_database(
        search_space=SearchSpace(database_schema=database),
        database_connector=object(),
        question=_question(),
    )

    assert database_profile_result.database_type == "DuckDB"
    assert database_profile_result.database_name == "example"
    assert [
        result.table_name
        for result in database_profile_result.table_profile_results
    ] == [
        "orders",
        "customers",
    ]
    assert [
        result.table_summary
        for result in database_profile_result.table_profile_results
    ] == [
        "orders summary.",
        "customers summary.",
    ]
    assert "Profiling database example with 2 tables" in caplog.text
    assert "Profiling 2 database tables with 2 workers" in caplog.text
    assert "Profiled database example with 2 table profiles" in caplog.text
