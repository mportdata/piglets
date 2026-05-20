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
