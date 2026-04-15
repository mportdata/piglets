from pydantic import BaseModel

from .database import Database, Table


class PruningColumns(BaseModel):
    """A list of columns for a given table in a pruning operation."""

    table: str = ""
    columns: list[str] = []


class PreservationColumns(PruningColumns):
    """A list of columns to be preserved for a given table."""


class PreservationSet(BaseModel):
    """The set of tables and fields to preserve during pruning, based on the logical plan and natural language question."""

    relevant_tables: list[str] = []
    relevant_columns: list[PreservationColumns] = []

    def to_database_type(self, target_database: Database) -> Database:
        """Convert the PreservationSet to a Database type, which can be used for pruning."""
        preserved_tables = []
        for table in target_database.tables:
            if table.name in self.relevant_tables:
                preserved_tables.append(table)
            else:
                relevant_columns_for_table = next(
                    (col.columns for col in self.relevant_columns if col.table == table.name),
                    []
                )
                if relevant_columns_for_table:
                    preserved_columns = [
                        column for column in table.columns
                        if column.name in relevant_columns_for_table
                    ]
                    preserved_tables.append(
                        Table(name=table.name, columns=preserved_columns)
                    )
        return Database(name=target_database.name, tables=preserved_tables)


class DeletionColumns(PruningColumns):
    """A list of columns to be deleted for a given table."""


class DeletionSet(BaseModel):
    """The set of tables and fields to delete during pruning, based on the logical plan and natural language question."""

    obviously_irrelevant_tables: list[str] = []
    obviously_irrelevant_columns: list[DeletionColumns] = []

    def to_database_type(self, target_database: Database) -> Database:
        """Convert the DeletionSet to a Database type, which can be used for pruning."""
        deleted_tables = []
        for table in target_database.tables:
            if table.name in self.obviously_irrelevant_tables:
                deleted_tables.append(table)
            else:
                irrelevant_columns_for_table = next(
                    (col.columns for col in self.obviously_irrelevant_columns if col.table == table.name),
                    []
                )
                if irrelevant_columns_for_table:
                    deleted_columns = [
                        column for column in table.columns
                        if column.name in irrelevant_columns_for_table
                    ]
                    deleted_tables.append(
                        Table(name=table.name, columns=deleted_columns)
                    )
        return Database(name=target_database.name, tables=deleted_tables)
