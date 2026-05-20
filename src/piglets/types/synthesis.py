from typing import Literal

from pydantic import BaseModel, Field

from .database import DatabaseSchema, TableSchema
from .queries import QueryResults


class RefinedSchemaColumn(BaseModel):
    """A column selected for the synthesized final schema."""

    column_name: str = Field(description="The selected column name.")
    relevance_reason: str = Field(
        description="Functional reason this column is needed."
    )


class RefinedSchemaTable(BaseModel):
    """Columns selected for a table in the synthesized final schema."""

    relevant_columns: list[RefinedSchemaColumn] = Field(
        default_factory=list,
        description="Columns selected for this table."
    )


class RejectedCandidate(BaseModel):
    """A candidate column explicitly rejected during synthesis."""

    table: str = Field(description="The table containing the rejected column.")
    column: str = Field(description="The rejected column name.")
    reject_reason: str = Field(description="Why the candidate was rejected.")


class SynthesisResult(BaseModel):
    """Structured output from the APEX-style synthesis prompt."""

    refined_schema: dict[str, RefinedSchemaTable] = Field(
        default_factory=dict,
        description="Final refined schema grouped by table name."
    )
    rejected_candidates: list[RejectedCandidate] = Field(
        default_factory=list,
        description="Candidate columns explicitly rejected during synthesis."
    )
    exploration_queries: list[str] = Field(
        default_factory=list,
        description="SQL queries requested when status is EXPLORING."
    )
    status: Literal["EXPLORING", "[CONFIRM]"] = Field(
        description="Whether synthesis needs exploration or is confirmed."
    )

    def to_database_schema(self, database_schema: DatabaseSchema) -> DatabaseSchema:
        """Convert selected schema output to a DatabaseSchema using known schema only."""
        selected_table_schemas = []
        table_schemas_by_name = {
            table_schema.name: table_schema
            for table_schema in database_schema.table_schemas
        }

        for table_name, refined_table in self.refined_schema.items():
            source_table_schema = table_schemas_by_name.get(table_name)
            if source_table_schema is None:
                continue

            selected_column_names = {
                column.column_name
                for column in refined_table.relevant_columns
            }
            selected_column_schemas = [
                column_schema for column_schema in source_table_schema.column_schemas
                if column_schema.name in selected_column_names
            ]
            if selected_column_schemas:
                selected_table_schemas.append(
                    TableSchema(
                        name=source_table_schema.name,
                        column_schemas=selected_column_schemas,
                    )
                )

        return DatabaseSchema(
            name=database_schema.name,
            database_type=database_schema.database_type,
            table_schemas=selected_table_schemas,
        )


class SynthesisRound(BaseModel):
    """One observable round of synthesis and optional exploration evidence."""

    round_number: int = Field(description="One-indexed synthesis round number.")
    synthesis_result: SynthesisResult = Field(
        description="Structured synthesis response for this round."
    )
    exploration_results: QueryResults | None = Field(
        default=None,
        description="Results from exploration queries requested in this round."
    )


class SynthesisRunResult(BaseModel):
    """A synthesis run containing the final result and round history."""

    final_result: SynthesisResult = Field(
        description="Final synthesis result returned by the loop."
    )
    rounds: list[SynthesisRound] = Field(
        default_factory=list,
        description="Observable synthesis rounds and exploration evidence."
    )
    reached_limit: bool = Field(
        default=False,
        description="Whether the loop stopped because max_refine_rounds was reached."
    )
