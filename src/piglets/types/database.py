from pydantic import BaseModel, Field


class Column(BaseModel):
    """The schema of a database column, including its name and data type."""

    name: str = Field(description="The name of the column.")
    data_type: str = Field(description="The data type of the column (e.g., INTEGER, VARCHAR).")

class Table(BaseModel):
    """The schema of a database table, including its name and columns."""

    name: str = Field(description="The name of the table.")
    columns: list[Column] = Field(description="The list of columns in the table.")

class Database(BaseModel):
    """The schema of a database, including its name and tables."""

    name: str = Field(description="The name of the database.")
    tables: list[Table] = Field(description="The list of tables in the database.")

    def subtract(self, database_to_subtract):
        """Subtract another database schema from this one, returning a new Database with only the tables and columns that are not in the other database."""
        remaining_tables = []
        for table in self.tables:
            if table.name not in [t.name for t in database_to_subtract.tables]:
                remaining_tables.append(table)
            else:
                other_table = next(t for t in database_to_subtract.tables if t.name == table.name)
                remaining_columns = [
                    column for column in table.columns
                    if column.name not in [c.name for c in other_table.columns]
                ]
                if remaining_columns:
                    remaining_tables.append(Table(name=table.name, columns=remaining_columns))
        return Database(name=self.name, tables=remaining_tables)

    def union(self, other_database):
        """Return a new Database containing all tables and columns from both databases without duplicates."""
        union_tables = []
        for table in self.tables:
            other_table = next(
                (t for t in other_database.tables if t.name == table.name),
                None,
            )
            if other_table is None:
                union_tables.append(table)
                continue

            column_names = {column.name for column in table.columns}
            union_columns = [
                *table.columns,
                *[
                    column for column in other_table.columns
                    if column.name not in column_names
                ],
            ]
            union_tables.append(Table(name=table.name, columns=union_columns))

        table_names = {table.name for table in self.tables}
        union_tables.extend(
            table for table in other_database.tables
            if table.name not in table_names
        )

        return Database(name=self.name, tables=union_tables)

    def export_as_string(self) -> str:
        """Export the database schema as a compact, readable string."""
        lines = [f"Database: {self.name}"]

        for table in self.tables:
            columns = ", ".join(
                f"{column.name}: {column.data_type}"
                for column in table.columns
            )
            lines.append(f"  Table: {table.name} (Columns: {columns})")
        return "\n".join(lines)
