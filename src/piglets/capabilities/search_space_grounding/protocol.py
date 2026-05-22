from typing import Protocol, runtime_checkable

from piglets.types import WorkflowState


@runtime_checkable
class SearchSpaceGrounder(Protocol):
    """A capability that grounds the workflow search space."""

    def ground(self, state: WorkflowState) -> WorkflowState:
        """Ground the search space in the provided workflow state."""
        ...
