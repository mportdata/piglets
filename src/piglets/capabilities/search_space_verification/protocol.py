from typing import Protocol, runtime_checkable

from piglets.types import WorkflowState


@runtime_checkable
class SearchSpaceVerifier(Protocol):
    """A capability that verifies a workflow search space."""

    def verify(self, state: WorkflowState) -> WorkflowState:
        """Verify the search space in the provided workflow state."""
        ...
