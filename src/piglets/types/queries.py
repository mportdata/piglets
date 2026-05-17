from typing import Any

from pydantic import BaseModel, Field


class SQLQuery(BaseModel):
    """A SQL Query."""

    query: str


class SQLQueries(BaseModel):
    """A list of SQL queries."""

    query: list[SQLQuery] = Field(default_factory=list)


class QueryResult(BaseModel):
    """Rows returned from executing a SQL query."""

    query: str
    columns: list[str] = Field(default_factory=list)
    rows: list[tuple[Any, ...]] = Field(default_factory=list)
    row_count: int = 0

    def rows_as_dicts(self) -> list[dict[str, Any]]:
        """Return rows keyed by column name for ergonomic downstream use."""
        return [
            dict(zip(self.columns, row))
            for row in self.rows
        ]

    def to_string(self, max_rows: int = 20, max_cell_length: int = 120) -> str:
        """Render a compact prompt-readable preview of the result rows."""
        if max_rows < 0:
            raise ValueError("max_rows must be greater than or equal to 0")
        if max_cell_length < 1:
            raise ValueError("max_cell_length must be greater than or equal to 1")

        rendered_rows = self.rows[:max_rows]
        lines = [
            f"Query: {self.query}",
            f"Rows returned: {self.row_count}",
            f"Rows shown: {len(rendered_rows)}",
        ]

        if not self.columns:
            return "\n".join(lines)

        lines.extend([
            "",
            self._format_table_row(self.columns, max_cell_length),
            self._format_table_row(["---"] * len(self.columns), max_cell_length),
        ])
        lines.extend(
            self._format_table_row(row, max_cell_length)
            for row in rendered_rows
        )

        if self.row_count > len(rendered_rows):
            lines.append(f"... truncated {self.row_count - len(rendered_rows)} rows")

        return "\n".join(lines)

    @classmethod
    def _format_table_row(cls, values: list[Any] | tuple[Any, ...], max_cell_length: int) -> str:
        return "| " + " | ".join(
            cls._format_cell(value, max_cell_length)
            for value in values
        ) + " |"

    @staticmethod
    def _format_cell(value: Any, max_cell_length: int) -> str:
        if value is None:
            cell = "NULL"
        else:
            cell = str(value)
        cell = cell.replace("\n", " ").replace("|", "\\|")
        if len(cell) > max_cell_length:
            cell = cell[: max_cell_length - 3] + "..."
        return cell
    
class QueryResults(BaseModel):
    """An array of SQL query results"""

    query_results: list[QueryResult] = Field(default_factory=list)

    def to_string(self, max_rows: int = 20, max_cell_length: int = 120) -> str:
        if not self.query_results:
            return "Query Results: 0"

        result_count = len(self.query_results)
        lines = [
            f"Query Results: {result_count}",
        ]

        for index, query_result in enumerate(self.query_results, start=1):
            lines.extend([
                "",
                f"Query Result {index} of {result_count}",
                query_result.to_string(
                    max_rows=max_rows,
                    max_cell_length=max_cell_length,
                ),
            ])

        return "\n".join(lines)


class ProfilingQuery(SQLQuery):
    """A single query generated for profiling the database."""

    motivation: str = ""


class ProfilingQueries(SQLQueries):
    """A list of queries generated for profiling the database."""

    query: list[ProfilingQuery] = Field(default_factory=list)
