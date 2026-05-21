from typing import Protocol, runtime_checkable

from piglets.types import WorkflowState


@runtime_checkable
class SearchSpaceReducer(Protocol):
    """A capability that reduces the workflow search space."""

    def reduce(self, state: WorkflowState) -> WorkflowState:
        """Reduce the search space in the provided workflow state."""
        ...
