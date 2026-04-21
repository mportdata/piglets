from .bigquery import BigQueryURL
from .url import URL

__all__ = ["BigQueryURL", "DuckDBURL", "MotherDuckURL", "SnowflakeURL", "URL"]


def __getattr__(name):
    if name == "DuckDBURL":
        from .duckdb import DuckDBURL

        return DuckDBURL
    if name == "MotherDuckURL":
        from .motherduck import MotherDuckURL

        return MotherDuckURL
    if name == "SnowflakeURL":
        from .snowflake import SnowflakeURL

        return SnowflakeURL
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
