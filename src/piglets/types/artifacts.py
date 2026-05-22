from typing import Any

from pydantic import BaseModel, Field

from .database import DatabaseSchema
from .linking import SemanticLinkingResult
from .profiling import DatabaseProfileResult
from .synthesis import SynthesisRunResult


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
    semantic_linking_result: SemanticLinkingResult | None = Field(
        default=None,
        description="Raw semantic linking output used to enrich the search space.",
    )
    database_profile_result: DatabaseProfileResult | None = Field(
        default=None,
        description="Empirical profile evidence for the current search space.",
    )
    synthesis_run_result: SynthesisRunResult | None = Field(
        default=None,
        description="Global synthesis result used to finalize the search space.",
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


class WorkflowState(BaseModel):
    """The artifact bundle passed between workflow stages."""

    question: Question | None = Field(
        default=None,
        description="The question being answered.",
    )
    search_space: SearchSpace = Field(
        default_factory=SearchSpace,
        description="The current workflow search space.",
    )
    hypothesis: Hypothesis | None = Field(
        default=None,
        description="The current generated hypothesis, if available.",
    )
