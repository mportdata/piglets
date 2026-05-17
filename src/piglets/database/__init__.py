from .database_connector import (
    DatabaseConnector as DatabaseConnector,
    database_name_from_connection as database_name_from_connection,
    database_name_from_connection_string as database_name_from_connection_string,
    database_type_from_connection as database_type_from_connection,
)
from .url import BigQueryURL as BigQueryURL, URL as URL

__all__ = [
    "BigQueryURL",
    "DatabaseConnector",
    "DuckDBURL",
    "MotherDuckURL",
    "SnowflakeURL",
    "URL",
    "database_name_from_connection",
    "database_name_from_connection_string",
    "database_type_from_connection",
]


def __getattr__(name):
    if name == "DuckDBURL":
        from .url import DuckDBURL

        return DuckDBURL
    if name == "MotherDuckURL":
        from .url import MotherDuckURL

        return MotherDuckURL
    if name == "SnowflakeURL":
        from .url import SnowflakeURL

        return SnowflakeURL
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
