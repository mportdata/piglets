from piglets.types import Question, WorkflowState

from .protocol import WorkflowStage


class WorkflowRunner:
    """Run workflow stages in order."""

    def __init__(self, stages: list[WorkflowStage]):
        self.stages = stages

    def run(self, question: Question) -> WorkflowState:
        state = WorkflowState(question=question)
        for stage in self.stages:
            state = stage.run(state)
        return state
