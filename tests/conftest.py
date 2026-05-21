import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from piglets import (
    AggregatePlan,
    DatabaseSchema,
    DatabaseConnector,
    DualPathwayPruner,
    LogicalPlan,
    LogicalPlanner,
    LogicalSteps,
    Question,
    SearchSpace,
    SemanticLinker,
    SemanticLinkingResult,
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
def question() -> Question:
    return Question(
        natural_language_question=(
            "Which manufacturers saw the largest increase in average revenue per "
            "order between 1996 and 1997, considering only manufacturers with at "
            "least 100 orders in both years, and excluding cancelled orders?"
        )
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

    billing_project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")

    from piglets import BigQueryURL

    database_connector = DatabaseConnector(
        connection=BigQueryURL(
            project_id="bigquery-public-data",
            dataset="stackoverflow",
            billing_project_id=billing_project_id,
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
    question: Question,
    logical_planner: LogicalPlanner,
) -> LogicalPlan:
    return logical_planner.plan(
        question=question,
    )


@pytest.fixture
def aggregate_logical_plan(
    question: Question,
    model_name: str,
) -> AggregatePlan:
    logical_planner = LogicalPlanner(model_name, num_samples=3)
    return logical_planner.plan(
        question=question,
    )

@pytest.fixture
def duckdb_database_schema(duckdb_connector) -> DatabaseSchema:
    return duckdb_connector.get_database_schema()


@pytest.fixture
def bigquery_database_schema(bigquery_connector) -> DatabaseSchema:
    return bigquery_connector.get_database_schema()


@pytest.fixture
def duckdb_search_space(duckdb_connector) -> SearchSpace:
    return duckdb_connector.add_to_search_space(SearchSpace())


@pytest.fixture
def bigquery_search_space(bigquery_connector) -> SearchSpace:
    return bigquery_connector.add_to_search_space(SearchSpace())

@pytest.fixture
def semantic_linker(model_name) -> SemanticLinker:
    return SemanticLinker(model_name=model_name)

@pytest.fixture
def dual_pathway_pruner(model_name) -> DualPathwayPruner:
    return DualPathwayPruner(model_name=model_name)

@pytest.fixture
def pruned_duckdb_search_space(
    dual_pathway_pruner,
    question,
    duckdb_search_space,
    aggregate_logical_plan,
) -> SearchSpace:
    return dual_pathway_pruner.dual_pathway_pruning(
        question=question,
        search_space=duckdb_search_space,
        logical_plan=aggregate_logical_plan,
    )


@pytest.fixture
def pruned_duckdb_database_schema(pruned_duckdb_search_space) -> DatabaseSchema:
    assert pruned_duckdb_search_space.database_schema is not None
    return pruned_duckdb_search_space.database_schema

@pytest.fixture
def semantic_linking_result(
    semantic_linker,
    question,
    pruned_duckdb_search_space,
    logical_plan,
) -> SemanticLinkingResult:
    return semantic_linker.link(
        question=question,
        search_space=pruned_duckdb_search_space,
        logical_plan=logical_plan,
    )
