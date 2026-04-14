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
