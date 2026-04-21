from sqlalchemy.engine.url import make_url

from duckdb_sqlalchemy import Dialect
from piglets.database.url.bigquery import BigQueryURL
from piglets.database.url.duckdb import DuckDBURL
from piglets.database.url.motherduck import MotherDuckURL
from piglets.database.url.snowflake import SnowflakeURL


def test_bigquery_url_uses_env_project_when_project_id_is_omitted(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT_ID", "env-project")

    assert BigQueryURL(dataset="dataset").render_as_string(hide_password=False) == (
        "bigquery://env-project/dataset"
    )
    assert BigQueryURL().render_as_string(hide_password=False) == "bigquery://env-project"


def test_bigquery_url_keeps_dataset_only_when_env_project_is_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT_ID", raising=False)

    assert (
        BigQueryURL(dataset="dataset").render_as_string(hide_password=False)
        == "bigquery:///dataset"
    )
    assert BigQueryURL().render_as_string(hide_password=False) == "bigquery://"


def test_bigquery_render_as_string_can_hide_credentials():
    connection = BigQueryURL(
        project_id="project",
        dataset="dataset",
        credentials_base64="secret",
    )

    assert "credentials_base64=%2A%2A%2A" in connection.render_as_string()
    assert "credentials_base64=secret" in connection.render_as_string(
        hide_password=False
    )


def test_snowflake_render_as_string_hides_password_by_default():
    connection = SnowflakeURL(
        account="account",
        user="user",
        password="secret/password",
        database="database",
        schema="schema",
        token="token-value",
        private_key_file_pwd="key-password",
    )

    safe_connection_string = connection.render_as_string()

    assert "secret" not in safe_connection_string
    assert "token-value" not in safe_connection_string
    assert "key-password" not in safe_connection_string
    assert "snowflake://user:***@account/database/schema" in safe_connection_string
    assert "private_key_file_pwd=%2A%2A%2A" in safe_connection_string
    assert "token=%2A%2A%2A" in safe_connection_string


def test_snowflake_render_as_string_can_keep_password():
    connection_string = SnowflakeURL(
        account="account",
        user="user",
        password="secret/password",
        database="database",
        schema="schema",
        token="token-value",
        private_key_file_pwd="key-password",
    ).render_as_string(hide_password=False)

    assert "secret%2Fpassword" in connection_string
    assert "token=token-value" in connection_string
    assert "private_key_file_pwd=key-password" in connection_string


def test_duckdb_url_defaults_to_memory_database():
    connection_string = DuckDBURL().render_as_string(hide_password=False)

    assert connection_string == "duckdb:///:memory:"

    _, opts = Dialect().create_connect_args(make_url(connection_string))
    assert opts["database"] == ":memory:"
    assert opts["url_config"] == {}


def test_duckdb_url_supports_file_database_and_config_params():
    connection_string = DuckDBURL(
        database="analytics.db",
        threads=4,
        memory_limit="1GB",
        access_mode="read_only",
        pool="queue",
    ).render_as_string(hide_password=False)

    url = make_url(connection_string)

    assert str(url) == (
        "duckdb:///analytics.db?access_mode=read_only&"
        "memory_limit=1GB&pool=queue&threads=4"
    )

    _, opts = Dialect().create_connect_args(url)
    assert opts["database"] == "analytics.db?access_mode=read_only"
    assert opts["url_config"] == {
        "memory_limit": "1GB",
        "threads": "4",
    }


def test_motherduck_url_normalizes_database_prefix():
    connection_string = MotherDuckURL(database="analytics").render_as_string(
        hide_password=False
    )

    assert connection_string == "duckdb:///md:analytics"

    _, opts = Dialect().create_connect_args(make_url(connection_string))
    assert opts["database"] == "md:analytics"
    assert opts["url_config"] == {}


def test_motherduck_url_splits_path_and_config_params_via_dialect():
    connection_string = MotherDuckURL(
        database="md:analytics",
        attach_mode="single",
        access_mode="read_only",
        session_name="team-a",
        memory_limit="1GB",
        threads=4,
        motherduck_token="token-value",
    ).render_as_string(hide_password=False)

    url = make_url(connection_string)

    assert str(url) == (
        "duckdb:///md:analytics?access_mode=read_only&attach_mode=single&"
        "memory_limit=1GB&motherduck_token=token-value&session_name=team-a&"
        "threads=4"
    )

    _, opts = Dialect().create_connect_args(url)
    assert opts["database"] == (
        "md:analytics?access_mode=read_only&attach_mode=single&session_name=team-a"
    )
    assert opts["url_config"] == {
        "memory_limit": "1GB",
        "motherduck_token": "token-value",
        "threads": "4",
    }


def test_motherduck_render_as_string_hides_tokens():
    connection = MotherDuckURL(
        database="analytics",
        motherduck_token="token-value",
        motherduck_oauth_token="oauth-value",
    )

    safe_connection_string = connection.render_as_string()

    assert "token-value" not in safe_connection_string
    assert "oauth-value" not in safe_connection_string
    assert "motherduck_token=%2A%2A%2A" in safe_connection_string
    assert "motherduck_oauth_token=%2A%2A%2A" in safe_connection_string
