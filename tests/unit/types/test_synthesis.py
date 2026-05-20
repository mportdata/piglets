import pytest
from pydantic import ValidationError

from piglets.types import (
    ColumnSchema,
    DatabaseSchema,
    RefinedSchemaColumn,
    RefinedSchemaTable,
    RejectedCandidate,
    SynthesisRound,
    SynthesisResult,
    SynthesisRunResult,
    TableSchema,
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
            ),
            TableSchema(
                name="customers",
                column_schemas=[
                    ColumnSchema(name="customer_id", data_type="INTEGER"),
                    ColumnSchema(name="name", data_type="VARCHAR"),
                ],
            ),
        ],
    )


def test_synthesis_result_can_confirm_refined_schema():
    result = SynthesisResult(
        refined_schema={
            "orders": RefinedSchemaTable(
                relevant_columns=[
                    RefinedSchemaColumn(
                        column_name="status",
                        relevance_reason="Needed for filtering cancelled orders.",
                    )
                ]
            )
        },
        rejected_candidates=[
            RejectedCandidate(
                table="orders",
                column="created_at",
                reject_reason="Not needed for the requested filter.",
            )
        ],
        exploration_queries=[],
        status="[CONFIRM]",
    )

    assert result.status == "[CONFIRM]"
    assert result.refined_schema["orders"].relevant_columns[0].column_name == "status"
    assert result.exploration_queries == []
    assert result.rejected_candidates[0].table == "orders"


def test_synthesis_result_can_request_exploration_queries():
    result = SynthesisResult(
        refined_schema={},
        rejected_candidates=[],
        exploration_queries=[
            "SELECT 1 FROM orders LIMIT 1",
        ],
        status="EXPLORING",
    )

    assert result.status == "EXPLORING"
    assert result.exploration_queries == ["SELECT 1 FROM orders LIMIT 1"]


def test_synthesis_result_rejects_invalid_status():
    with pytest.raises(ValidationError):
        SynthesisResult(status="DONE")


def test_synthesis_result_to_database_schema_uses_known_schema_only():
    result = SynthesisResult(
        refined_schema={
            "orders": RefinedSchemaTable(
                relevant_columns=[
                    RefinedSchemaColumn(
                        column_name="status",
                        relevance_reason="Needed for filtering cancelled orders.",
                    ),
                    RefinedSchemaColumn(
                        column_name="hallucinated_column",
                        relevance_reason="Not present in schema.",
                    ),
                ]
            ),
            "hallucinated_table": RefinedSchemaTable(
                relevant_columns=[
                    RefinedSchemaColumn(
                        column_name="anything",
                        relevance_reason="Not present in schema.",
                    )
                ]
            ),
        },
        rejected_candidates=[],
        exploration_queries=[],
        status="[CONFIRM]",
    )

    synthesized_database = result.to_database_schema(_database())

    assert synthesized_database.name == "example"
    assert synthesized_database.database_type == "DuckDB"
    assert len(synthesized_database.table_schemas) == 1
    assert synthesized_database.table_schemas[0].name == "orders"
    assert [column.name for column in synthesized_database.table_schemas[0].column_schemas] == [
        "status",
    ]


def test_synthesis_run_result_packs_final_result_and_round_history():
    result = SynthesisResult(
        refined_schema={},
        rejected_candidates=[],
        exploration_queries=[],
        status="[CONFIRM]",
    )
    synthesis_run = SynthesisRunResult(
        final_result=result,
        rounds=[
            SynthesisRound(
                round_number=1,
                synthesis_result=result,
            )
        ],
        reached_limit=False,
    )

    assert synthesis_run.final_result is result
    assert synthesis_run.rounds[0].round_number == 1
    assert synthesis_run.rounds[0].exploration_results is None
    assert synthesis_run.reached_limit is False
