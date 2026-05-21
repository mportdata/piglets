from piglets import (
    ColumnSchema,
    DatabaseSchema,
    DualPathwayPruner,
    Hypothesis,
    Question,
    SearchSpace,
    SearchSpaceReducer,
    TableSchema,
    WorkflowState,
)
from piglets.capabilities.search_space_reduction import (
    DualPathwayPruner as CapabilityDualPathwayPruner,
    SearchSpaceReducer as CapabilitySearchSpaceReducer,
)
from piglets.types import DeletionColumns, DeletionSet, PreservationSet


def _question() -> Question:
    return Question(natural_language_question="count piglets")


def _database_schema() -> DatabaseSchema:
    return DatabaseSchema(
        name="example",
        database_type="DuckDB",
        table_schemas=[
            TableSchema(
                name="piglets",
                column_schemas=[
                    ColumnSchema(name="piglet_id", data_type="INTEGER"),
                    ColumnSchema(name="piglet_name", data_type="VARCHAR"),
                ],
            )
        ],
    )


class FakeDualPathwayPruner(DualPathwayPruner):
    def __init__(self):
        super().__init__(model_name="fake-model")
        self.preservation_prompt_contexts = []
        self.deletion_prompt_contexts = []

    def _get_tables_and_fields_to_preserve(
        self,
        question: Question,
        search_space: SearchSpace,
        prompt_context: str = "",
    ) -> PreservationSet:
        self.preservation_prompt_contexts.append(prompt_context)
        return PreservationSet()

    def _get_tables_and_fields_to_delete(
        self,
        question: Question,
        search_space: SearchSpace,
        prompt_context: str = "",
    ) -> DeletionSet:
        self.deletion_prompt_contexts.append(prompt_context)
        return DeletionSet(
            obviously_irrelevant_columns=[
                DeletionColumns(table="piglets", columns=["piglet_name"])
            ]
        )


def test_search_space_reduction_imports_are_exported():
    assert DualPathwayPruner is CapabilityDualPathwayPruner
    assert SearchSpaceReducer is CapabilitySearchSpaceReducer


def test_dual_pathway_pruner_matches_search_space_reducer_protocol():
    assert isinstance(FakeDualPathwayPruner(), SearchSpaceReducer)


def test_dual_pathway_pruner_reduce_returns_state_with_reduced_search_space():
    question = _question()
    hypothesis = Hypothesis(
        question=question,
        content="Use the piglets table.",
        technique="fake_generation",
    )
    state = WorkflowState(
        question=question,
        search_space=SearchSpace(database_schema=_database_schema()),
        hypothesis=hypothesis,
    )

    dual_pathway_pruner = FakeDualPathwayPruner()

    updated_state = dual_pathway_pruner.reduce(state)

    assert updated_state is not state
    assert updated_state.question == question
    assert updated_state.hypothesis == hypothesis
    assert updated_state.search_space is not state.search_space
    assert updated_state.search_space.database_schema is not None
    assert updated_state.search_space.database_schema.table_schemas[0].column_schemas == [
        ColumnSchema(name="piglet_id", data_type="INTEGER")
    ]
    assert dual_pathway_pruner.preservation_prompt_contexts == [
        "*** HYPOTHESIS ***\nUse the piglets table."
    ]
    assert dual_pathway_pruner.deletion_prompt_contexts == [
        "*** HYPOTHESIS ***\nUse the piglets table."
    ]
