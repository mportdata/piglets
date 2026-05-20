from typing import Protocol, runtime_checkable

from piglets.types import Hypothesis, Question


@runtime_checkable
class HypothesisGenerator(Protocol):
    """A capability that generates a hypothesis for a question."""

    def generate(self, question: Question) -> Hypothesis:
        """Generate a hypothesis for the provided question."""
        ...
