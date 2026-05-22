from typing import Protocol, runtime_checkable

from piglets.types import WorkflowState


@runtime_checkable
class SearchSpaceFinalizer(Protocol):
    """A capability that finalizes a workflow search space."""

    def finalize(self, state: WorkflowState) -> WorkflowState:
        """Finalize the search space in the provided workflow state."""
        ...
