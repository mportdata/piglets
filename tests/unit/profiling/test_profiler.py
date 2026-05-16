from piglets.policies import SemanticRules
from piglets.profiling.profiler import Profiler
from piglets.types import (
    Column,
    ProfilingQueries,
    ProfilingQuery,
    SemanticLinkingResult,
    Table,
)


class FakeProfilingLLM:
    def __init__(self):
        self.prompts = []
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return ProfilingQueries(
            exploratory_queries=[
                ProfilingQuery(
                    motivation="Check status values.",
                    query="SELECT DISTINCT status FROM orders LIMIT 10",
                )
            ]
        )


def _table() -> Table:
    return Table(
        name="orders",
        columns=[
            Column(name="order_id", data_type="INTEGER"),
            Column(name="status", data_type="VARCHAR"),
            Column(name="created_at", data_type="TIMESTAMP"),
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


def test_profile_table_uses_structured_output_and_returns_profiling_queries(monkeypatch):
    fake_llm = FakeProfilingLLM()
    init_calls = []

    def fake_init_chat_model(model, model_provider=None):
        init_calls.append((model, model_provider))
        return fake_llm

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        fake_init_chat_model,
    )

    profiler = Profiler(model_name="test-model", model_provider="test-provider")
    profiling_queries = profiler.profile_table(
        natural_language_query="Which orders are cancelled?",
        database_type="duckdb",
        table=_table(),
        semantic_linking_result=_semantic_linking_result(),
    )

    assert init_calls == [("test-model", "test-provider")]
    assert fake_llm.schema is ProfilingQueries
    assert isinstance(profiling_queries, ProfilingQueries)
    assert len(profiling_queries.exploratory_queries) == 1
    assert profiling_queries.exploratory_queries[0].motivation
    assert profiling_queries.exploratory_queries[0].query


def test_profile_table_prompt_uses_critical_rules_and_single_table_guidance(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(model_name="test-model", rules=SemanticRules())
    profiler.profile_table(
        natural_language_query="Which orders are cancelled?",
        database_type="duckdb",
        table=_table(),
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
    assert "exploratory_queries" in prompt
    assert "motivation" in prompt
    assert "query" in prompt


def test_profile_table_prompt_uses_case_insensitive_table_function_lookup(monkeypatch):
    fake_llm = FakeProfilingLLM()

    monkeypatch.setattr(
        "piglets.profiling.profiler.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    profiler = Profiler(model_name="test-model")
    profiler.profile_table(
        natural_language_query="Which orders are cancelled?",
        database_type="duckdb",
        table=Table(
            name="Orders",
            columns=[
                Column(name="status", data_type="VARCHAR"),
            ],
        ),
        semantic_linking_result=_semantic_linking_result(table_name="orders"),
    )

    assert "Contains order-level facts and status fields." in fake_llm.prompts[0]
