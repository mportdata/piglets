from pydantic import BaseModel, Field


class TableProfileColumnResult(BaseModel):
    """Structured profiling analysis for one table column."""

    column_name: str = Field(description="The column name.")
    relevance_reason: str = Field(
        description="Why this column is relevant to the user question."
    )
    observations: str = Field(
        description="Factual findings from executed profiling queries."
    )


class TableProfileResult(BaseModel):
    """Structured profiling analysis for one database table."""

    relevant: bool = Field(
        description="Whether the table is relevant to the user question."
    )
    relevant_columns: list[TableProfileColumnResult] = Field(default_factory=list)
    table_summary: str = Field(
        description="Concise summary of what the table represents in context."
    )
