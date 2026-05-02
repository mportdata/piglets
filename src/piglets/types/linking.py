from pydantic import BaseModel, Field


class SemanticLinkingResult(BaseModel):
    """Structured output describing how a query maps onto the database schema."""

    database_structure: str = Field(
        description="Overview of the database structure relevant to the user query."
    )
    query_specific_content_analysis: str = Field(
        description="Detailed analysis mapping the query intent to tables, columns, filters, and joins."
    )
    table_functions: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of table name to its functional role for the query."
    )
