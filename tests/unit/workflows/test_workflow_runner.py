from piglets import (
    ColumnSchema,
    DatabaseSchema,
    GenerateHypothesis,
    Hypothesis,
    LoadSearchSpace,
    Question,
    ReduceSearchSpace,
    SearchSpace,
    TableSchema,
    WorkflowRunner,
    WorkflowState,
    WorkflowStage,
)
from piglets.workflows import (
    GenerateHypothesis as WorkflowGenerateHypothesis,
    LoadSearchSpace as WorkflowLoadSearchSpace,
    ReduceSearchSpace as WorkflowReduceSearchSpace,
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


class FakeSearchSpaceReducer:
    def __init__(self):
        self.states = []

    def reduce(self, state: WorkflowState) -> WorkflowState:
        self.states.append(state)
        return state.model_copy(
            update={
                "search_space": SearchSpace(
                    database_schema=DatabaseSchema(
                        name="reduced",
                        database_type="DuckDB",
                        table_schemas=[],
                    )
                )
            }
        )


class RecordingStage:
    def __init__(self, name: str, calls: list[str]):
        self.name = name
        self.calls = calls

    def run(self, state: WorkflowState) -> WorkflowState:
        self.calls.append(self.name)
        return state


def test_workflow_imports_are_exported():
    assert WorkflowRunner is WorkflowWorkflowRunner
    assert WorkflowStage is WorkflowWorkflowStage
    assert LoadSearchSpace is WorkflowLoadSearchSpace
    assert GenerateHypothesis is WorkflowGenerateHypothesis
    assert ReduceSearchSpace is WorkflowReduceSearchSpace


def test_load_search_space_stage_adds_database_schema_to_state():
    connector = FakeDatabaseConnector()
    state = WorkflowState(question=_question())

    updated_state = LoadSearchSpace(connector).run(state)

    assert updated_state is not state
    assert connector.search_spaces == [state.search_space]
    assert updated_state.question == state.question
    assert updated_state.search_space.database_schema == _database_schema()
    assert state.search_space.database_schema is None


def test_generate_hypothesis_stage_adds_hypothesis_to_state():
    generator = FakeHypothesisGenerator()
    question = _question()
    state = WorkflowState(question=question)

    updated_state = GenerateHypothesis(generator).run(state)

    assert updated_state is not state
    assert generator.questions == [question]
    assert updated_state.question == question
    assert updated_state.hypothesis is not None
    assert updated_state.hypothesis.question == question
    assert updated_state.hypothesis.content == "Count rows in the piglets table."
    assert updated_state.hypothesis.technique == "fake_generation"
    assert state.hypothesis is None


def test_reduce_search_space_stage_updates_state_search_space():
    reducer = FakeSearchSpaceReducer()
    state = WorkflowState(
        question=_question(),
        search_space=SearchSpace(database_schema=_database_schema()),
    )

    updated_state = ReduceSearchSpace(reducer).run(state)

    assert updated_state is not state
    assert reducer.states == [state]
    assert updated_state.question == state.question
    assert updated_state.search_space.database_schema == DatabaseSchema(
        name="reduced",
        database_type="DuckDB",
        table_schemas=[],
    )
    assert state.search_space.database_schema == _database_schema()


def test_workflow_runner_runs_stages_in_order():
    calls = []
    question = _question()
    runner = WorkflowRunner(
        stages=[
            RecordingStage("first", calls),
            RecordingStage("second", calls),
        ]
    )

    state = runner.run(question)

    assert calls == ["first", "second"]
    assert isinstance(state, WorkflowState)
    assert state.question == question


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

    state = runner.run(question)

    assert state.question == question
    assert state.search_space.database_schema == _database_schema()
    assert state.hypothesis is not None
    assert state.hypothesis.question == question
    assert state.hypothesis.technique == "fake_generation"


def test_workflow_runner_loads_generates_hypothesis_and_reduces_search_space():
    connector = FakeDatabaseConnector()
    generator = FakeHypothesisGenerator()
    reducer = FakeSearchSpaceReducer()
    question = _question()
    runner = WorkflowRunner(
        stages=[
            LoadSearchSpace(connector),
            GenerateHypothesis(generator),
            ReduceSearchSpace(reducer),
        ]
    )

    state = runner.run(question)

    assert reducer.states[0].search_space.database_schema == _database_schema()
    assert reducer.states[0].hypothesis is not None
    assert state.question == question
    assert state.search_space.database_schema == DatabaseSchema(
        name="reduced",
        database_type="DuckDB",
        table_schemas=[],
    )
    assert state.hypothesis is not None
    assert state.hypothesis.technique == "fake_generation"
