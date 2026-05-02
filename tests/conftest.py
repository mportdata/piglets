import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from piglets import (
    AggregatePlan,
    Database,
    DatabaseConnector,
    LogicalPlan,
    LogicalPlanner,
    LogicalSteps,
)


class FakeLLM:
    def __init__(self):
        self.prompts = []
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self


class FakeLogicalPlanLLM(FakeLLM):
    def invoke(self, prompt):
        self.prompts.append(prompt)
        schema = self.schema or LogicalSteps
        return schema(logical_steps=["1. Count piglets."])


@pytest.fixture
def fake_logical_plan_llm() -> FakeLogicalPlanLLM:
    return FakeLogicalPlanLLM()


@pytest.fixture
def model_name() -> str:
    return "gpt-5.2"

@pytest.fixture
def natural_language_query() -> str:
    return (
        "Which manufacturers saw the largest increase in average revenue per "
        "order between 1996 and 1997, considering only manufacturers with at "
        "least 100 orders in both years, and excluding cancelled orders?"
    )

@pytest.fixture
def logical_planner(model_name) -> LogicalPlanner:
    return LogicalPlanner(model_name)

@pytest.fixture(scope="session")
def example_duckdb_path(tmp_path_factory) -> Path:
    pytest.importorskip("duckdb")

    from piglets import create_tpch_example_duckdb_db

    db_path = tmp_path_factory.mktemp("duckdb") / "tpch_sf001.duckdb"
    return create_tpch_example_duckdb_db(
        db_path=db_path,
        scale_factor=0.01,
    )


@pytest.fixture
def duckdb_connector(example_duckdb_path: Path):
    pytest.importorskip("duckdb_sqlalchemy")

    from piglets import DuckDBURL

    database_connector = DatabaseConnector(
        connection=DuckDBURL(database=str(example_duckdb_path)),
    )
    return database_connector


@pytest.fixture
def bigquery_connector():
    pytest.importorskip("sqlalchemy_bigquery")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")

    missing_env_vars = []
    if not project_id:
        missing_env_vars.append("GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_PROJECT_ID")
    if not dataset:
        missing_env_vars.append("BIGQUERY_DATASET")
    if missing_env_vars:
        pytest.skip(
            "BigQuery integration requires "
            + ", ".join(missing_env_vars)
        )

    from piglets import BigQueryURL

    database_connector = DatabaseConnector(
        connection=BigQueryURL(
            project_id=project_id,
            dataset=dataset,
        ),
    )
    return database_connector


@pytest.fixture
def snowflake_connector():
    pytest.importorskip("snowflake.sqlalchemy")

    required_env_vars = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
    ]
    missing_env_vars = [
        env_var for env_var in required_env_vars
        if not os.getenv(env_var)
    ]
    if missing_env_vars:
        pytest.skip(
            "Snowflake integration requires "
            + ", ".join(missing_env_vars)
        )

    from piglets import SnowflakeURL

    database_connector = DatabaseConnector(
        connection=SnowflakeURL(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database="SNOWFLAKE_SAMPLE_DATA",
            schema="TPCH_SF1",
        ),
    )
    return database_connector


@pytest.fixture
def logical_plan(
    natural_language_query: str,
    logical_planner: LogicalPlanner,
) -> LogicalPlan:
    return logical_planner.plan(
        natural_language_query=natural_language_query,
        num_samples=1,
    )


@pytest.fixture
def aggregate_logical_plan(
    natural_language_query: str,
    logical_planner: LogicalPlanner,
) -> AggregatePlan:
    return logical_planner.plan(
        natural_language_query=natural_language_query,
        num_samples=3,
    )


@pytest.fixture
def duckdb_database(duckdb_connector) -> Database:
    return duckdb_connector.get_database_schema()


@pytest.fixture
def bigquery_database(bigquery_connector) -> Database:
    return bigquery_connector.get_database_schema()
