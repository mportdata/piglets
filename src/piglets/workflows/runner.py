from piglets.types import WorkflowState

from .protocol import WorkflowStage


class WorkflowRunner:
    """Run workflow stages in order."""

    def __init__(self, stages: list[WorkflowStage]):
        self.stages = stages

    def run(self, state: WorkflowState | None = None) -> WorkflowState:
        if state is None:
            state = WorkflowState()
        for stage in self.stages:
            state = stage.run(state)
        return state
