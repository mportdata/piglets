from typing import Protocol

from piglets.types import WorkflowContext


class WorkflowStage(Protocol):
    """A workflow stage that transforms a workflow context."""

    def run(self, context: WorkflowContext) -> WorkflowContext:
        """Run the stage and return the updated workflow context."""
        ...
