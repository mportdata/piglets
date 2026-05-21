from piglets.capabilities.hypothesis_generation import HypothesisGenerator
from piglets.capabilities.search_space_reduction import SearchSpaceReducer
from piglets.database import DatabaseConnector
from piglets.types import WorkflowState


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
        return state.model_copy(
            update={
                "hypothesis": self.hypothesis_generator.generate(state.question)
            }
        )


class ReduceSearchSpace:
    """Reduce the workflow search space."""

    def __init__(self, search_space_reducer: SearchSpaceReducer):
        self.search_space_reducer = search_space_reducer

    def run(self, state: WorkflowState) -> WorkflowState:
        return self.search_space_reducer.reduce(state)
