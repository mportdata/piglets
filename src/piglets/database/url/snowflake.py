from typing import Any
from urllib.parse import quote_plus


class SnowflakeURL:
    def __init__(
        self,
        account: str,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
        schema: str | None = None,
        warehouse: str | None = None,
        role: str | None = None,
        authenticator: str | None = None,
        token: str | None = None,
        private_key_file: str | None = None,
        private_key_file_pwd: str | None = None,
        host: str | None = None,
        port: int | None = None,
        protocol: str | None = None,
        region: str | None = None,
        login_timeout: int | None = None,
        network_timeout: int | None = None,
        client_session_keep_alive: bool | None = None,
        extra_query: dict[str, str | int | bool] | None = None,
    ):
        self.account = account
        self.user = user
        self.password = password
        self.database = database
        self.schema = schema
        self.warehouse = warehouse
        self.role = role
        self.authenticator = authenticator
        self.token = token
        self.private_key_file = private_key_file
        self.private_key_file_pwd = private_key_file_pwd
        self.host = host
        self.port = port
        self.protocol = protocol
        self.region = region
        self.login_timeout = login_timeout
        self.network_timeout = network_timeout
        self.client_session_keep_alive = client_session_keep_alive
        self.extra_query = extra_query or {}

    @staticmethod
    def _quote_password(password: str) -> str:
        return password.replace("%", "%25").replace(":", "%3A").replace("@", "%40").replace("/", "%2F")

    @staticmethod
    def _format_bool(value: bool) -> str:
        return "True" if value else "False"

    @staticmethod
    def _format_query_value(value: Any) -> str:
        if isinstance(value, bool):
            return SnowflakeURL._format_bool(value)
        return str(value)

    def _query_parameters(self, hide_password: bool = False) -> dict[str, str]:
        token = "***" if hide_password and self.token else self.token
        private_key_file_pwd = (
            "***"
            if hide_password and self.private_key_file_pwd
            else self.private_key_file_pwd
        )
        query = {
            "warehouse": self.warehouse,
            "role": self.role,
            "authenticator": self.authenticator,
            "token": token,
            "private_key_file": self.private_key_file,
            "private_key_file_pwd": private_key_file_pwd,
            "protocol": self.protocol,
            "login_timeout": self.login_timeout,
            "network_timeout": self.network_timeout,
            "client_session_keep_alive": self.client_session_keep_alive,
            **self.extra_query,
        }
        return {
            key: self._format_query_value(value)
            for key, value in query.items()
            if value is not None
        }

    def render_as_string(self, hide_password: bool = True) -> str:
        if self.schema and not self.database:
            raise ValueError("schema cannot be specified without database")

        user = quote_plus(self.user or "")
        password = "***" if hide_password and self.password else self.password or ""
        password = self._quote_password(password)

        if self.host:
            host = self.host
            port = self.port or 443
            connection_string = f"snowflake://{user}:{password}@{host}:{port}/"
        elif self.region:
            connection_string = (
                f"snowflake://{user}:{password}@{self.account}.{self.region}/"
            )
        else:
            connection_string = f"snowflake://{user}:{password}@{self.account}/"

        if self.database:
            connection_string += quote_plus(self.database)
            if self.schema:
                connection_string += "/" + quote_plus(self.schema)

        query = self._query_parameters(hide_password=hide_password)
        if self.host:
            query["account"] = self.account
        if query:
            query_string = "&".join(
                f"{key}={quote_plus(value)}" for key, value in sorted(query.items())
            )
            connection_string += "?" + query_string

        return connection_string
