from piglets import (
    ColumnSchema,
    DatabaseSchema,
    Hypothesis,
    Question,
    SearchSpace,
    SearchSpaceGrounder,
    SemanticLinker,
    SemanticLinkingResult,
    TableSchema,
    WorkflowState,
)
from piglets.capabilities.search_space_grounding import (
    SearchSpaceGrounder as CapabilitySearchSpaceGrounder,
    SemanticLinker as CapabilitySemanticLinker,
)


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
                ],
            ),
            TableSchema(
                name="owners",
                column_schemas=[
                    ColumnSchema(name="owner_id", data_type="INTEGER"),
                ],
            ),
        ],
    )


class FakeSemanticLinker(SemanticLinker):
    def __init__(self):
        super().__init__(model_name="fake-model")
        self.calls = []

    def link(
        self,
        question: Question,
        search_space: SearchSpace,
        hypothesis: Hypothesis | None = None,
    ) -> SemanticLinkingResult:
        self.calls.append(
            {
                "question": question,
                "search_space": search_space,
                "hypothesis": hypothesis,
            }
        )
        return SemanticLinkingResult(
            database_structure="A small piglet database.",
            query_specific_content_analysis="Piglets is the target table.",
            table_functions={
                "PIGLETS": "Target table for piglet counts.",
            },
        )


def test_search_space_grounding_imports_are_exported():
    assert SemanticLinker is CapabilitySemanticLinker
    assert SearchSpaceGrounder is CapabilitySearchSpaceGrounder


def test_semantic_linker_matches_search_space_grounder_protocol():
    assert isinstance(FakeSemanticLinker(), SearchSpaceGrounder)


def test_semantic_linker_ground_adds_schema_annotations_and_raw_result():
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
    semantic_linker = FakeSemanticLinker()

    updated_state = semantic_linker.ground(state)

    assert updated_state is not state
    assert semantic_linker.calls == [
        {
            "question": question,
            "search_space": state.search_space,
            "hypothesis": hypothesis,
        }
    ]
    assert updated_state.question == question
    assert updated_state.hypothesis == hypothesis
    assert updated_state.search_space is not state.search_space
    assert updated_state.search_space.semantic_linking_result is not None
    assert (
        updated_state.search_space.semantic_linking_result.database_structure
        == "A small piglet database."
    )

    database_schema = updated_state.search_space.database_schema
    assert database_schema is not None
    assert database_schema.name == "example"
    assert database_schema.semantic_annotation is not None
    assert (
        database_schema.semantic_annotation.query_specific_content_analysis
        == "Piglets is the target table."
    )
    assert database_schema.table_schemas[0].semantic_annotation is not None
    assert (
        database_schema.table_schemas[0].semantic_annotation.function
        == "Target table for piglet counts."
    )
    assert database_schema.table_schemas[1].semantic_annotation is None
    assert state.search_space.database_schema == _database_schema()
