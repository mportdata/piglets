from pydantic import BaseModel, Field

from .database import Database, Table


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

    table_name: str = Field(description="The table name.")
    relevant: bool = Field(
        description="Whether the table is relevant to the user question."
    )
    relevant_columns: list[TableProfileColumnResult] = Field(default_factory=list)
    table_summary: str = Field(
        description="Concise summary of what the table represents in context."
    )

    def to_string(self, table: Table) -> str:
        """Render table profile evidence in the APEX schema-status shape."""
        status = "[MARKED RELEVANT]" if self.relevant else "[MARKED IRRELEVANT]"
        relevant_columns_by_name = {
            column_result.column_name: column_result
            for column_result in self.relevant_columns
        }

        lines = [
            f"Table: {table.name} {status}",
            "Columns:",
        ]

        for column in table.columns:
            column_result = relevant_columns_by_name.get(column.name)
            observations = (
                column_result.observations
                if column_result
                else self.table_summary
            )
            reason = (
                column_result.relevance_reason
                if column_result
                else "No column-level relevance reason identified."
            )
            lines.extend([
                f"{column.name} ({column.data_type}):",
                f"Observations: {observations}",
                f"Reason: {reason}",
            ])

        return "\n".join(lines)


class DatabaseProfileResult(BaseModel):
    """A collection of table profile results for a given database."""

    database_type: str = Field(
        description="The type of database."
    )
    database_name: str = Field(
        description="The name of the database."
    )
    table_profile_results: list[TableProfileResult] = Field(default_factory=list)

    def to_string(self, database: Database) -> str:
        """Render database profile evidence alongside the provided schema."""
        profiles_by_table_name = {
            table_profile_result.table_name: table_profile_result
            for table_profile_result in self.table_profile_results
        }
        lines = [
            f"Database Profile: {self.database_name}",
            f"Database Type: {self.database_type}",
            f"Table Profiles: {len(self.table_profile_results)}",
        ]

        for table in database.tables:
            table_profile_result = profiles_by_table_name.get(table.name)
            lines.append("")
            if table_profile_result:
                lines.append(table_profile_result.to_string(table))
            else:
                lines.append(self._unknown_table_to_string(table))

        return "\n".join(lines)

    @staticmethod
    def _unknown_table_to_string(table: Table) -> str:
        lines = [
            f"Table: {table.name} [MARKED UNKNOWN]",
            "Columns:",
        ]

        for column in table.columns:
            lines.extend([
                f"{column.name} ({column.data_type}):",
                "Observations: No empirical profile evidence available for this table.",
                "Reason: No profiling decision available.",
            ])

        return "\n".join(lines)
