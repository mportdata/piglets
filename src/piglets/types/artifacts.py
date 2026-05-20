from typing import Any

from pydantic import BaseModel, Field

from .database import DatabaseSchema


class Question(BaseModel):
    """A natural language question to answer against a database."""

    natural_language_question: str = Field(
        description="The user's natural language question."
    )


class SearchSpace(BaseModel):
    """The currently available search space for a text-to-SQL workflow."""

    database_schema: DatabaseSchema | None = Field(
        default=None,
        description="The database schema currently available to the workflow.",
    )


class Hypothesis(BaseModel):
    """A generated hypothesis for how to answer a question."""

    question: Question = Field(description="The question this hypothesis addresses.")
    content: str = Field(description="Prompt-readable hypothesis content.")
    technique: str = Field(description="The technique that generated the hypothesis.")
    technique_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters used by the generating technique.",
    )


class WorkflowContext(BaseModel):
    """The artifact bundle passed between workflow stages."""

    question: Question = Field(description="The question being answered.")
    search_space: SearchSpace = Field(
        default_factory=SearchSpace,
        description="The current workflow search space.",
    )
    hypothesis: Hypothesis | None = Field(
        default=None,
        description="The current generated hypothesis, if available.",
    )
