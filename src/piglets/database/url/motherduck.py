from collections.abc import Mapping
from typing import Any

from duckdb_sqlalchemy import URL as DuckDBSQLAlchemyURL


class MotherDuckURL:
    def __init__(
        self,
        database: str,
        attach_mode: str | None = None,
        access_mode: str | None = None,
        session_name: str | None = None,
        motherduck_token: str | None = None,
        motherduck_oauth_token: str | None = None,
        threads: int | None = None,
        memory_limit: str | None = None,
        pool: str | None = None,
        path_query: Mapping[str, Any] | None = None,
        extra_query: Mapping[str, Any] | None = None,
    ):
        self.database = self._normalize_database(database)
        self.attach_mode = attach_mode
        self.access_mode = access_mode
        self.session_name = session_name
        self.motherduck_token = motherduck_token
        self.motherduck_oauth_token = motherduck_oauth_token
        self.threads = threads
        self.memory_limit = memory_limit
        self.pool = pool
        self.path_query = path_query or {}
        self.extra_query = extra_query or {}

    @staticmethod
    def _normalize_database(database: str) -> str:
        if database.startswith(("md:", "motherduck:")):
            return database
        return f"md:{database}"

    def _path_parameters(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "attach_mode": self.attach_mode,
                "access_mode": self.access_mode,
                "session_name": self.session_name,
                **self.path_query,
            }.items()
            if value is not None
        }

    def _query_parameters(self, hide_password: bool = False) -> dict[str, Any]:
        motherduck_token = "***" if hide_password and self.motherduck_token else self.motherduck_token
        motherduck_oauth_token = (
            "***"
            if hide_password and self.motherduck_oauth_token
            else self.motherduck_oauth_token
        )
        return {
            key: value
            for key, value in {
                "motherduck_token": motherduck_token,
                "motherduck_oauth_token": motherduck_oauth_token,
                "threads": self.threads,
                "memory_limit": self.memory_limit,
                "pool": self.pool,
                **self.extra_query,
            }.items()
            if value is not None
        }

    def render_as_string(self, hide_password: bool = True) -> str:
        return str(
            DuckDBSQLAlchemyURL(
                database=self.database,
                query={
                    **self._path_parameters(),
                    **self._query_parameters(hide_password=hide_password),
                },
            )
        )


__all__ = ["MotherDuckURL"]
