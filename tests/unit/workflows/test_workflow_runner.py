from piglets import (
    ColumnSchema,
    DatabaseSchema,
    GenerateHypothesis,
    Hypothesis,
    LoadSearchSpace,
    Question,
    SearchSpace,
    TableSchema,
    WorkflowContext,
    WorkflowRunner,
    WorkflowStage,
)
from piglets.workflows import (
    GenerateHypothesis as WorkflowGenerateHypothesis,
    LoadSearchSpace as WorkflowLoadSearchSpace,
    WorkflowRunner as WorkflowWorkflowRunner,
    WorkflowStage as WorkflowWorkflowStage,
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
            )
        ],
    )


class FakeDatabaseConnector:
    def __init__(self):
        self.search_spaces = []

    def add_to_search_space(self, search_space: SearchSpace) -> SearchSpace:
        self.search_spaces.append(search_space)
        return SearchSpace(database_schema=_database_schema())


class FakeHypothesisGenerator:
    def __init__(self):
        self.questions = []

    def generate(self, question: Question) -> Hypothesis:
        self.questions.append(question)
        return Hypothesis(
            question=question,
            content="Count rows in the piglets table.",
            technique="fake_generation",
            technique_parameters={"fake": True},
        )


class RecordingStage:
    def __init__(self, name: str, calls: list[str]):
        self.name = name
        self.calls = calls

    def run(self, context: WorkflowContext) -> WorkflowContext:
        self.calls.append(self.name)
        return context


def test_workflow_imports_are_exported():
    assert WorkflowRunner is WorkflowWorkflowRunner
    assert WorkflowStage is WorkflowWorkflowStage
    assert LoadSearchSpace is WorkflowLoadSearchSpace
    assert GenerateHypothesis is WorkflowGenerateHypothesis


def test_load_search_space_stage_adds_database_schema_to_context():
    connector = FakeDatabaseConnector()
    context = WorkflowContext(question=_question())

    updated_context = LoadSearchSpace(connector).run(context)

    assert updated_context is not context
    assert connector.search_spaces == [context.search_space]
    assert updated_context.question == context.question
    assert updated_context.search_space.database_schema == _database_schema()
    assert context.search_space.database_schema is None


def test_generate_hypothesis_stage_adds_hypothesis_to_context():
    generator = FakeHypothesisGenerator()
    question = _question()
    context = WorkflowContext(question=question)

    updated_context = GenerateHypothesis(generator).run(context)

    assert updated_context is not context
    assert generator.questions == [question]
    assert updated_context.question == question
    assert updated_context.hypothesis is not None
    assert updated_context.hypothesis.question == question
    assert updated_context.hypothesis.content == "Count rows in the piglets table."
    assert updated_context.hypothesis.technique == "fake_generation"
    assert context.hypothesis is None


def test_workflow_runner_runs_stages_in_order():
    calls = []
    question = _question()
    runner = WorkflowRunner(
        stages=[
            RecordingStage("first", calls),
            RecordingStage("second", calls),
        ]
    )

    context = runner.run(question)

    assert calls == ["first", "second"]
    assert isinstance(context, WorkflowContext)
    assert context.question == question


def test_workflow_runner_loads_search_space_and_generates_hypothesis():
    connector = FakeDatabaseConnector()
    generator = FakeHypothesisGenerator()
    question = _question()
    runner = WorkflowRunner(
        stages=[
            LoadSearchSpace(connector),
            GenerateHypothesis(generator),
        ]
    )

    context = runner.run(question)

    assert context.question == question
    assert context.search_space.database_schema == _database_schema()
    assert context.hypothesis is not None
    assert context.hypothesis.question == question
    assert context.hypothesis.technique == "fake_generation"
