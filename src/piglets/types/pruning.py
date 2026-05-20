from pydantic import BaseModel, Field

from .database import DatabaseSchema, TableSchema


class PruningColumns(BaseModel):
    """A list of columns for a given table in a pruning operation."""

    table: str = ""
    columns: list[str] = Field(default_factory=list)


class PreservationColumns(PruningColumns):
    """A list of columns to be preserved for a given table."""


class PreservationSet(BaseModel):
    """The set of tables and fields to preserve during pruning, based on the logical plan and natural language question."""

    relevant_tables: list[str] = Field(default_factory=list)
    relevant_columns: list[PreservationColumns] = Field(default_factory=list)

    def to_database_schema(self, target_database_schema: DatabaseSchema) -> DatabaseSchema:
        """Convert the PreservationSet to a DatabaseSchema type, which can be used for pruning."""
        preserved_table_schemas = []
        for table_schema in target_database_schema.table_schemas:
            if table_schema.name in self.relevant_tables:
                preserved_table_schemas.append(table_schema)
            else:
                relevant_columns_for_table_schema = next(
                    (
                        col.columns for col in self.relevant_columns
                        if col.table == table_schema.name
                    ),
                    []
                )
                if relevant_columns_for_table_schema:
                    preserved_column_schemas = [
                        column_schema for column_schema in table_schema.column_schemas
                        if column_schema.name in relevant_columns_for_table_schema
                    ]
                    preserved_table_schemas.append(
                        TableSchema(
                            name=table_schema.name,
                            column_schemas=preserved_column_schemas,
                        )
                    )
        return DatabaseSchema(
            name=target_database_schema.name,
            database_type=target_database_schema.database_type,
            table_schemas=preserved_table_schemas,
        )


class DeletionColumns(PruningColumns):
    """A list of columns to be deleted for a given table."""


class DeletionSet(BaseModel):
    """The set of tables and fields to delete during pruning, based on the logical plan and natural language question."""

    obviously_irrelevant_tables: list[str] = Field(default_factory=list)
    obviously_irrelevant_columns: list[DeletionColumns] = Field(default_factory=list)

    def to_database_schema(self, target_database_schema: DatabaseSchema) -> DatabaseSchema:
        """Convert the DeletionSet to a DatabaseSchema type, which can be used for pruning."""
        deleted_table_schemas = []
        for table_schema in target_database_schema.table_schemas:
            if table_schema.name in self.obviously_irrelevant_tables:
                deleted_table_schemas.append(table_schema)
            else:
                irrelevant_columns_for_table_schema = next(
                    (
                        col.columns for col in self.obviously_irrelevant_columns
                        if col.table == table_schema.name
                    ),
                    []
                )
                if irrelevant_columns_for_table_schema:
                    deleted_column_schemas = [
                        column_schema for column_schema in table_schema.column_schemas
                        if column_schema.name in irrelevant_columns_for_table_schema
                    ]
                    deleted_table_schemas.append(
                        TableSchema(
                            name=table_schema.name,
                            column_schemas=deleted_column_schemas,
                        )
                    )
        return DatabaseSchema(
            name=target_database_schema.name,
            database_type=target_database_schema.database_type,
            table_schemas=deleted_table_schemas,
        )
