from typing import Protocol, runtime_checkable

from piglets.types import WorkflowState


@runtime_checkable
class SearchSpaceEnricher(Protocol):
    """A capability that enriches the workflow search space."""

    def enrich(self, state: WorkflowState) -> WorkflowState:
        """Enrich the search space in the provided workflow state."""
        ...
