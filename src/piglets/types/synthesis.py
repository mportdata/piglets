from typing import Literal

from pydantic import BaseModel, Field

from .database import Database, Table
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

    def to_database_type(self, database: Database) -> Database:
        """Convert selected schema output to a Database using known schema only."""
        selected_tables = []
        tables_by_name = {table.name: table for table in database.tables}

        for table_name, refined_table in self.refined_schema.items():
            source_table = tables_by_name.get(table_name)
            if source_table is None:
                continue

            selected_column_names = {
                column.column_name
                for column in refined_table.relevant_columns
            }
            selected_columns = [
                column for column in source_table.columns
                if column.name in selected_column_names
            ]
            if selected_columns:
                selected_tables.append(
                    Table(name=source_table.name, columns=selected_columns)
                )

        return Database(
            name=database.name,
            database_type=database.database_type,
            tables=selected_tables,
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
