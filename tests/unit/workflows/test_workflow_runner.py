import pytest

from piglets import (
    ColumnSchema,
    DatabaseSchema,
    EnterUserQuestion,
    FinalizeSearchSpace,
    GroundSearchSpace,
    GenerateHypothesis,
    Hypothesis,
    LoadSearchSpace,
    Question,
    ReduceSearchSpace,
    SearchSpace,
    TableSchema,
    VerifySearchSpace,
    WorkflowRunner,
    WorkflowState,
    WorkflowStage,
)
from piglets.workflows import (
    EnterUserQuestion as WorkflowEnterUserQuestion,
    FinalizeSearchSpace as WorkflowFinalizeSearchSpace,
    GroundSearchSpace as WorkflowGroundSearchSpace,
    GenerateHypothesis as WorkflowGenerateHypothesis,
    LoadSearchSpace as WorkflowLoadSearchSpace,
    ReduceSearchSpace as WorkflowReduceSearchSpace,
    VerifySearchSpace as WorkflowVerifySearchSpace,
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


class FakeSearchSpaceGrounder:
    def __init__(self):
        self.states = []

    def ground(self, state: WorkflowState) -> WorkflowState:
        self.states.append(state)
        return state.model_copy(
            update={
                "search_space": SearchSpace(
                    database_schema=DatabaseSchema(
                        name="enriched",
                        database_type="DuckDB",
                        table_schemas=[],
                    )
                )
            }
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


class FakeSearchSpaceVerifier:
    def __init__(self):
        self.states = []

    def verify(self, state: WorkflowState) -> WorkflowState:
        self.states.append(state)
        return state.model_copy(
            update={
                "search_space": SearchSpace(
                    database_schema=DatabaseSchema(
                        name="verified",
                        database_type="DuckDB",
                        table_schemas=[],
                    )
                )
            }
        )


class FakeSearchSpaceFinalizer:
    def __init__(self):
        self.states = []

    def finalize(self, state: WorkflowState) -> WorkflowState:
        self.states.append(state)
        return state.model_copy(
            update={
                "search_space": SearchSpace(
                    database_schema=DatabaseSchema(
                        name="finalized",
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
    assert EnterUserQuestion is WorkflowEnterUserQuestion
    assert LoadSearchSpace is WorkflowLoadSearchSpace
    assert GenerateHypothesis is WorkflowGenerateHypothesis
    assert GroundSearchSpace is WorkflowGroundSearchSpace
    assert ReduceSearchSpace is WorkflowReduceSearchSpace
    assert VerifySearchSpace is WorkflowVerifySearchSpace
    assert FinalizeSearchSpace is WorkflowFinalizeSearchSpace


def test_enter_user_question_stage_adds_question_to_state():
    question = _question()
    state = WorkflowState(search_space=SearchSpace(database_schema=_database_schema()))

    updated_state = EnterUserQuestion(question).run(state)

    assert updated_state is not state
    assert updated_state.question == question
    assert updated_state.search_space == state.search_space
    assert state.question is None


def test_enter_user_question_stage_accepts_string():
    state = WorkflowState()

    updated_state = EnterUserQuestion("count piglets").run(state)

    assert updated_state.question == _question()
    assert state.question is None


def test_enter_user_question_stage_preserves_existing_artifacts():
    question = _question()
    hypothesis = Hypothesis(
        question=question,
        content="Count rows in the piglets table.",
        technique="fake_generation",
    )
    state = WorkflowState(
        search_space=SearchSpace(database_schema=_database_schema()),
        hypothesis=hypothesis,
    )

    updated_state = EnterUserQuestion(question).run(state)

    assert updated_state.question == question
    assert updated_state.search_space == state.search_space
    assert updated_state.hypothesis == hypothesis


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


def test_generate_hypothesis_stage_requires_question():
    generator = FakeHypothesisGenerator()
    state = WorkflowState()

    with pytest.raises(ValueError, match="WorkflowState must contain a question"):
        GenerateHypothesis(generator).run(state)

    assert generator.questions == []


def test_ground_search_space_stage_updates_state_search_space():
    grounder = FakeSearchSpaceGrounder()
    state = WorkflowState(
        question=_question(),
        search_space=SearchSpace(database_schema=_database_schema()),
    )

    updated_state = GroundSearchSpace(grounder).run(state)

    assert updated_state is not state
    assert grounder.states == [state]
    assert updated_state.question == state.question
    assert updated_state.search_space.database_schema == DatabaseSchema(
        name="enriched",
        database_type="DuckDB",
        table_schemas=[],
    )
    assert state.search_space.database_schema == _database_schema()


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


def test_verify_search_space_stage_updates_state_search_space():
    verifier = FakeSearchSpaceVerifier()
    state = WorkflowState(
        question=_question(),
        search_space=SearchSpace(database_schema=_database_schema()),
    )

    updated_state = VerifySearchSpace(verifier).run(state)

    assert updated_state is not state
    assert verifier.states == [state]
    assert updated_state.question == state.question
    assert updated_state.search_space.database_schema == DatabaseSchema(
        name="verified",
        database_type="DuckDB",
        table_schemas=[],
    )
    assert state.search_space.database_schema == _database_schema()


def test_finalize_search_space_stage_updates_state_search_space():
    finalizer = FakeSearchSpaceFinalizer()
    state = WorkflowState(
        question=_question(),
        search_space=SearchSpace(database_schema=_database_schema()),
    )

    updated_state = FinalizeSearchSpace(finalizer).run(state)

    assert updated_state is not state
    assert finalizer.states == [state]
    assert updated_state.question == state.question
    assert updated_state.search_space.database_schema == DatabaseSchema(
        name="finalized",
        database_type="DuckDB",
        table_schemas=[],
    )
    assert state.search_space.database_schema == _database_schema()


def test_workflow_runner_runs_stages_in_order():
    calls = []
    runner = WorkflowRunner(
        stages=[
            RecordingStage("first", calls),
            RecordingStage("second", calls),
        ]
    )

    state = runner.run()

    assert calls == ["first", "second"]
    assert isinstance(state, WorkflowState)
    assert state.question is None


def test_workflow_runner_can_start_from_existing_state():
    calls = []
    question = _question()
    initial_state = WorkflowState(question=question)
    runner = WorkflowRunner(stages=[RecordingStage("first", calls)])

    state = runner.run(initial_state)

    assert calls == ["first"]
    assert state == initial_state
    assert state.question == question


def test_workflow_runner_accepts_question_directly():
    calls = []
    runner = WorkflowRunner(stages=[RecordingStage("first", calls)])

    state = runner.run(question="count piglets")

    assert calls == ["first"]
    assert state.question == _question()


def test_workflow_runner_preserves_matching_state_question():
    calls = []
    question = _question()
    initial_state = WorkflowState(question=question)
    runner = WorkflowRunner(stages=[RecordingStage("first", calls)])

    state = runner.run(initial_state, question=question)

    assert calls == ["first"]
    assert state == initial_state
    assert state.question == question


def test_workflow_runner_rejects_conflicting_question():
    runner = WorkflowRunner(stages=[])
    state = WorkflowState(question=Question(natural_language_question="other"))

    with pytest.raises(ValueError, match="differs from the provided question"):
        runner.run(state, question="count piglets")


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

    state = runner.run(question=question)

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

    state = runner.run(question=question)

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
