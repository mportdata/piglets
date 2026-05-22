from pydantic import BaseModel, Field


class DatabaseSemanticAnnotation(BaseModel):
    """Query-specific semantic annotation for a database schema."""

    database_structure: str | None = Field(
        default=None,
        description="Semantic overview of the database structure for the current query.",
    )
    query_specific_content_analysis: str | None = Field(
        default=None,
        description="Query-specific analysis of how database content maps to user intent.",
    )


class TableSemanticAnnotation(BaseModel):
    """Query-specific semantic annotation for a table schema."""

    function: str | None = Field(
        default=None,
        description="Functional role of the table for the current query.",
    )


class ColumnSchema(BaseModel):
    """The schema of a database column, including its name and data type."""

    name: str = Field(description="The name of the column.")
    data_type: str = Field(description="The data type of the column (e.g., INTEGER, VARCHAR).")

class TableSchema(BaseModel):
    """The schema of a database table, including its name and columns."""

    name: str = Field(description="The name of the table.")
    column_schemas: list[ColumnSchema] = Field(
        description="The list of column schemas in the table."
    )
    semantic_annotation: TableSemanticAnnotation | None = Field(
        default=None,
        description="Query-specific semantic annotation for the table.",
    )

    def columns_to_string(self) -> str:
        """Export the table columns as one prompt-readable line per column."""
        return "\n".join(
            f"{column_schema.name} ({column_schema.data_type}):"
            for column_schema in self.column_schemas
        )

class DatabaseSchema(BaseModel):
    """The schema of a database, including its name and tables."""

    name: str = Field(description="The name of the database.")
    database_type: str = Field(description="The SQL database type or dialect.")
    table_schemas: list[TableSchema] = Field(
        description="The list of table schemas in the database."
    )
    semantic_annotation: DatabaseSemanticAnnotation | None = Field(
        default=None,
        description="Query-specific semantic annotation for the database.",
    )

    def subtract(self, database_schema_to_subtract: "DatabaseSchema") -> "DatabaseSchema":
        """Subtract another database schema from this one, returning a new DatabaseSchema with only the tables and columns that are not in the other database."""
        remaining_table_schemas = []
        for table_schema in self.table_schemas:
            if table_schema.name not in [
                t.name for t in database_schema_to_subtract.table_schemas
            ]:
                remaining_table_schemas.append(table_schema)
            else:
                other_table_schema = next(
                    t
                    for t in database_schema_to_subtract.table_schemas
                    if t.name == table_schema.name
                )
                remaining_column_schemas = [
                    column_schema for column_schema in table_schema.column_schemas
                    if column_schema.name not in [
                        c.name for c in other_table_schema.column_schemas
                    ]
                ]
                if remaining_column_schemas:
                    remaining_table_schemas.append(
                        TableSchema(
                            name=table_schema.name,
                            column_schemas=remaining_column_schemas,
                            semantic_annotation=table_schema.semantic_annotation,
                        )
                    )
        return DatabaseSchema(
            name=self.name,
            database_type=self.database_type,
            table_schemas=remaining_table_schemas,
            semantic_annotation=self.semantic_annotation,
        )

    def union(self, other_database_schema: "DatabaseSchema") -> "DatabaseSchema":
        """Return a new DatabaseSchema containing all tables and columns from both databases without duplicates."""
        union_table_schemas = []
        for table_schema in self.table_schemas:
            other_table_schema = next(
                (
                    t for t in other_database_schema.table_schemas
                    if t.name == table_schema.name
                ),
                None,
            )
            if other_table_schema is None:
                union_table_schemas.append(table_schema)
                continue

            column_schema_names = {
                column_schema.name for column_schema in table_schema.column_schemas
            }
            union_column_schemas = [
                *table_schema.column_schemas,
                *[
                    column_schema for column_schema in other_table_schema.column_schemas
                    if column_schema.name not in column_schema_names
                ],
            ]
            union_table_schemas.append(
                TableSchema(
                    name=table_schema.name,
                    column_schemas=union_column_schemas,
                    semantic_annotation=table_schema.semantic_annotation,
                )
            )

        table_schema_names = {table_schema.name for table_schema in self.table_schemas}
        union_table_schemas.extend(
            table_schema for table_schema in other_database_schema.table_schemas
            if table_schema.name not in table_schema_names
        )

        return DatabaseSchema(
            name=self.name,
            database_type=self.database_type,
            table_schemas=union_table_schemas,
            semantic_annotation=self.semantic_annotation,
        )

    def export_as_string(self) -> str:
        """Export the database schema as a compact, readable string."""
        lines = [
            f"Database: {self.name}",
            f"Database Type: {self.database_type}",
        ]

        for table_schema in self.table_schemas:
            columns = ", ".join(
                f"{column_schema.name}: {column_schema.data_type}"
                for column_schema in table_schema.column_schemas
            )
            lines.append(f"  Table: {table_schema.name} (Columns: {columns})")
        return "\n".join(lines)
