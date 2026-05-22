import logging

import pytest
from pydantic import ValidationError

from piglets.capabilities.search_space_finalization import GlobalSynthesizer
from piglets.types import (
    ColumnSchema,
    DatabaseSchema,
    DatabaseProfileResult,
    Question,
    QueryResult,
    RefinedSchemaColumn,
    RefinedSchemaTable,
    SearchSpace,
    SemanticLinkingResult,
    SynthesisResult,
    SynthesisRunResult,
    TableSchema,
    TableProfileColumnResult,
    TableProfileResult,
)


def _question() -> Question:
    return Question(natural_language_question="Which orders are cancelled?")


class FakeSynthesisLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []
        self.schema = None
        self.structured_output_method = None

    def with_structured_output(self, schema, method=None):
        self.schema = schema
        self.structured_output_method = method
        return self

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return self.responses.pop(0)


class FakeConnector:
    def __init__(self):
        self.queries = []

    def execute_query(self, query):
        self.queries.append(query)
        return QueryResult(
            query=query,
            columns=["value"],
            rows=[("observed",)],
            row_count=1,
        )


def _confirmed_result(column_name: str = "status") -> SynthesisResult:
    return SynthesisResult(
        refined_schema={
            "orders": RefinedSchemaTable(
                relevant_columns=[
                    RefinedSchemaColumn(
                        column_name=column_name,
                        relevance_reason="Needed for filtering cancelled orders.",
                    )
                ]
            )
        },
        rejected_candidates=[],
        exploration_queries=[],
        status="[CONFIRM]",
    )


def _exploring_result(
    exploration_queries: list[str] | None = None,
) -> SynthesisResult:
    queries = (
        ["SELECT DISTINCT status FROM orders LIMIT 10"]
        if exploration_queries is None
        else exploration_queries
    )
    return SynthesisResult(
        refined_schema={},
        rejected_candidates=[],
        exploration_queries=queries,
        status="EXPLORING",
    )


def _database() -> DatabaseSchema:
    return DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="orders",
                column_schemas=[
                    ColumnSchema(name="order_id", data_type="INTEGER"),
                    ColumnSchema(name="status", data_type="VARCHAR"),
                ],
            )
        ],
    )


def _database_profile_result() -> DatabaseProfileResult:
    return DatabaseProfileResult(
        database_name="example",
        database_type="DuckDB",
        table_profile_results=[
            TableProfileResult(
                table_name="orders",
                relevant=True,
                relevant_columns=[
                    TableProfileColumnResult(
                        column_name="status",
                        relevance_reason="Needed for filtering cancelled orders.",
                        observations="Values include cancelled and complete.",
                    )
                ],
                table_summary="Order table relevant to cancellation analysis.",
            )
        ],
    )


def _semantic_linking_result() -> SemanticLinkingResult:
    return SemanticLinkingResult(
        database_structure="Order database.",
        query_specific_content_analysis="Question maps to order status.",
        table_functions={
            "orders": "Contains order status fields.",
        },
    )


def _synthesizer(fake_connector: FakeConnector) -> GlobalSynthesizer:
    return GlobalSynthesizer(
        search_space=SearchSpace(database_schema=_database()),
        database_connector=fake_connector,
        model_name="test-model",
        model_provider="test-provider",
    )


def _synthesize(synthesizer: GlobalSynthesizer, **kwargs):
    return synthesizer.synthesize_observations(
        question=_question(),
        semantic_linking_result=_semantic_linking_result(),
        database_profile_result=_database_profile_result(),
        max_refine_rounds=3,
        **kwargs,
    )


def test_synthesizer_returns_history_by_default_for_first_round_confirm(monkeypatch):
    fake_llm = FakeSynthesisLLM([_confirmed_result()])
    fake_connector = FakeConnector()
    init_calls = []

    def fake_init_chat_model(model, model_provider=None):
        init_calls.append((model, model_provider))
        return fake_llm

    monkeypatch.setattr(
        "piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer.init_chat_model",
        fake_init_chat_model,
    )

    synthesis_run = _synthesize(_synthesizer(fake_connector))
    prompt = fake_llm.prompts[0]

    assert init_calls == [("test-model", "test-provider")]
    assert fake_llm.schema is SynthesisResult
    assert fake_llm.structured_output_method == "function_calling"
    assert isinstance(synthesis_run, SynthesisRunResult)
    assert synthesis_run.final_result.status == "[CONFIRM]"
    assert synthesis_run.reached_limit is False
    assert len(synthesis_run.rounds) == 1
    assert synthesis_run.rounds[0].round_number == 1
    assert synthesis_run.rounds[0].exploration_results is None
    assert fake_connector.queries == []
    assert "*** SCHEMA STATUS ***" in prompt
    assert "Table: orders [MARKED RELEVANT]" in prompt
    assert "status (VARCHAR):" in prompt
    assert "This is round 1 of 3." in prompt


def test_synthesizer_explores_and_feeds_results_into_next_prompt(monkeypatch):
    fake_llm = FakeSynthesisLLM([
        _exploring_result(),
        _confirmed_result(column_name="order_id"),
    ])
    fake_connector = FakeConnector()
    monkeypatch.setattr(
        "piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    synthesis_run = _synthesize(_synthesizer(fake_connector))

    assert isinstance(synthesis_run, SynthesisRunResult)
    assert synthesis_run.final_result.status == "[CONFIRM]"
    assert synthesis_run.final_result.refined_schema["orders"].relevant_columns[
        0
    ].column_name == "order_id"
    assert fake_connector.queries == ["SELECT DISTINCT status FROM orders LIMIT 10"]
    assert len(synthesis_run.rounds) == 2
    assert synthesis_run.rounds[0].exploration_results is not None
    assert synthesis_run.rounds[0].exploration_results.query_results[0].query == (
        "SELECT DISTINCT status FROM orders LIMIT 10"
    )
    assert "*** PREVIOUS SYNTHESIS ATTEMPTS ***" in fake_llm.prompts[1]
    assert "Round 1" in fake_llm.prompts[1]
    assert "Status: EXPLORING" in fake_llm.prompts[1]
    assert "Exploration Results:" in fake_llm.prompts[1]
    assert "observed" in fake_llm.prompts[1]


def test_synthesizer_can_return_final_result_without_history(monkeypatch):
    fake_llm = FakeSynthesisLLM([_confirmed_result()])
    fake_connector = FakeConnector()
    monkeypatch.setattr(
        "piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    synthesis_result = _synthesize(
        _synthesizer(fake_connector),
        return_history=False,
    )

    assert isinstance(synthesis_result, SynthesisResult)
    assert synthesis_result.status == "[CONFIRM]"


def test_synthesizer_stops_at_max_refine_rounds(monkeypatch):
    fake_llm = FakeSynthesisLLM([_exploring_result()])
    fake_connector = FakeConnector()
    monkeypatch.setattr(
        "piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )
    synthesizer = _synthesizer(fake_connector)

    synthesis_run = synthesizer.synthesize_observations(
        question=_question(),
        semantic_linking_result=_semantic_linking_result(),
        database_profile_result=_database_profile_result(),
        max_refine_rounds=1,
    )

    assert isinstance(synthesis_run, SynthesisRunResult)
    assert synthesis_run.final_result.status == "EXPLORING"
    assert synthesis_run.reached_limit is True
    assert len(synthesis_run.rounds) == 1
    assert synthesis_run.rounds[0].exploration_results is None
    assert fake_connector.queries == []


def test_synthesizer_stops_when_exploring_without_queries(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer")
    fake_llm = FakeSynthesisLLM([_exploring_result(exploration_queries=[])])
    fake_connector = FakeConnector()
    monkeypatch.setattr(
        "piglets.capabilities.search_space_finalization.techniques.global_synthesis.global_synthesizer.init_chat_model",
        lambda model, model_provider=None: fake_llm,
    )

    synthesis_run = _synthesize(_synthesizer(fake_connector))

    assert isinstance(synthesis_run, SynthesisRunResult)
    assert synthesis_run.final_result.status == "EXPLORING"
    assert synthesis_run.reached_limit is False
    assert len(synthesis_run.rounds) == 1
    assert synthesis_run.rounds[0].exploration_results is None
    assert fake_connector.queries == []
    assert "Synthesis requested exploration in round 1 without queries" in caplog.text


def test_synthesis_result_rejects_invalid_status_before_synthesizer_branching():
    with pytest.raises(ValidationError):
        SynthesisResult(status="DONE")
