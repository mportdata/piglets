from collections.abc import Mapping
from typing import Any

from duckdb_sqlalchemy import URL as DuckDBSQLAlchemyURL


class DuckDBURL:
    def __init__(
        self,
        database: str = ":memory:",
        threads: int | None = None,
        memory_limit: str | None = None,
        access_mode: str | None = None,
        pool: str | None = None,
        extra_query: Mapping[str, Any] | None = None,
    ):
        self.database = database
        self.threads = threads
        self.memory_limit = memory_limit
        self.access_mode = access_mode
        self.pool = pool
        self.extra_query = extra_query or {}

    def _query_parameters(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "threads": self.threads,
                "memory_limit": self.memory_limit,
                "access_mode": self.access_mode,
                "pool": self.pool,
                **self.extra_query,
            }.items()
            if value is not None
        }

    def render_as_string(self, hide_password: bool = True) -> str:
        return str(
            DuckDBSQLAlchemyURL(
                database=self.database,
                query=self._query_parameters(),
            )
        )


__all__ = ["DuckDBURL"]
