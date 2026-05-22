from piglets.capabilities.hypothesis_generation import HypothesisGenerator
from piglets.capabilities.search_space_finalization import SearchSpaceFinalizer
from piglets.capabilities.search_space_grounding import SearchSpaceGrounder
from piglets.capabilities.search_space_reduction import SearchSpaceReducer
from piglets.capabilities.search_space_verification import SearchSpaceVerifier
from piglets.database import DatabaseConnector
from piglets.types import Question, WorkflowState


def _require_question(state: WorkflowState) -> Question:
    if state.question is None:
        raise ValueError("WorkflowState must contain a question")
    return state.question


class EnterUserQuestion:
    """Enter the user question into the workflow state."""

    def __init__(self, question: Question | str):
        self.question = (
            question
            if isinstance(question, Question)
            else Question(natural_language_question=question)
        )

    def run(self, state: WorkflowState) -> WorkflowState:
        return state.model_copy(update={"question": self.question})


class LoadSearchSpace:
    """Load database schema into the workflow search space."""

    def __init__(self, database_connector: DatabaseConnector):
        self.database_connector = database_connector

    def run(self, state: WorkflowState) -> WorkflowState:
        return state.model_copy(
            update={
                "search_space": self.database_connector.add_to_search_space(
                    state.search_space
                )
            }
        )


class GenerateHypothesis:
    """Generate a hypothesis for the workflow question."""

    def __init__(self, hypothesis_generator: HypothesisGenerator):
        self.hypothesis_generator = hypothesis_generator

    def run(self, state: WorkflowState) -> WorkflowState:
        question = _require_question(state)
        return state.model_copy(
            update={
                "hypothesis": self.hypothesis_generator.generate(question)
            }
        )


class GroundSearchSpace:
    """Ground the workflow search space."""

    def __init__(self, search_space_grounder: SearchSpaceGrounder):
        self.search_space_grounder = search_space_grounder

    def run(self, state: WorkflowState) -> WorkflowState:
        _require_question(state)
        return self.search_space_grounder.ground(state)


class ReduceSearchSpace:
    """Reduce the workflow search space."""

    def __init__(self, search_space_reducer: SearchSpaceReducer):
        self.search_space_reducer = search_space_reducer

    def run(self, state: WorkflowState) -> WorkflowState:
        _require_question(state)
        return self.search_space_reducer.reduce(state)


class VerifySearchSpace:
    """Verify the workflow search space against table content."""

    def __init__(self, search_space_verifier: SearchSpaceVerifier):
        self.search_space_verifier = search_space_verifier

    def run(self, state: WorkflowState) -> WorkflowState:
        _require_question(state)
        return self.search_space_verifier.verify(state)


class FinalizeSearchSpace:
    """Finalize the workflow search space."""

    def __init__(self, search_space_finalizer: SearchSpaceFinalizer):
        self.search_space_finalizer = search_space_finalizer

    def run(self, state: WorkflowState) -> WorkflowState:
        _require_question(state)
        return self.search_space_finalizer.finalize(state)
