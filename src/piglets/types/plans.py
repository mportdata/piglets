from typing import TypedDict

class LogicalPlan(TypedDict):
    """A logical plan for how to answer a natural language query."""
    logical_steps: list[str]