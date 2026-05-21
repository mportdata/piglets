from typing import Protocol

from piglets.types import WorkflowState


class WorkflowStage(Protocol):
    """A workflow stage that transforms workflow state."""

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run the stage and return the updated workflow state."""
        ...
