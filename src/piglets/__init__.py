from .database import (
    BigQueryURL as BigQueryURL,
    DatabaseConnector as DatabaseConnector,
    URL as URL,
    database_name_from_connection as database_name_from_connection,
    database_name_from_connection_string as database_name_from_connection_string,
    database_type_from_connection as database_type_from_connection,
)
from .planning import LogicalPlanner as LogicalPlanner
from .policies import RuleMode as RuleMode
from .policies import SemanticRules as SemanticRules
from .profiling import Profiler as Profiler
from .pruning import Pruner as Pruner
from .semantic_linking import SemanticLinker as SemanticLinker
from .types import (
    AggregatePlan as AggregatePlan,
    Database as Database,
    DeletionColumns as DeletionColumns,
    DeletionSet as DeletionSet,
    LogicalPlan as LogicalPlan,
    LogicalPlans as LogicalPlans,
    LogicalSteps as LogicalSteps,
    PreservationColumns as PreservationColumns,
    PreservationSet as PreservationSet,
    ProfilingQuery as ProfilingQuery,
    ProfilingQueries as ProfilingQueries,
    QueryResult as QueryResult,
    QueryResults as QueryResults,
    PruningColumns as PruningColumns,
    SemanticLinkingResult as SemanticLinkingResult,
    SQLQueries as SQLQueries,
    SQLQuery as SQLQuery,
    TableProfileColumnResult as TableProfileColumnResult,
    TableProfileResult as TableProfileResult,
    Table as Table,
)

__all__ = [
    # Database
    "BigQueryURL",
    "DatabaseConnector",
    "DuckDBURL",
    "MotherDuckURL",
    "SnowflakeURL",
    "URL",
    "database_name_from_connection",
    "database_name_from_connection_string",
    "database_type_from_connection",
    "create_tpch_example_duckdb_db",
    # Planning
    "LogicalPlanner",
    "SemanticLinker",
    "RuleMode",
    "SemanticRules",
    # Types
    "AggregatePlan",
    "Database",
    "DeletionColumns",
    "DeletionSet",
    "LogicalPlan",
    "LogicalPlans",
    "LogicalSteps",
    "PreservationColumns",
    "PreservationSet",
    "PruningColumns",
    "QueryResult",
    "QueryResults",
    "SemanticLinkingResult",
    "SQLQueries",
    "SQLQuery",
    "TableProfileColumnResult",
    "TableProfileResult",
    "Table",
    # Pruning
    "Pruner",
    # Profiling
    "Profiler",
    "ProfilingQuery",
    "ProfilingQueries",
]


def __getattr__(name):
    if name == "DuckDBURL":
        from .database import DuckDBURL

        return DuckDBURL
    if name == "MotherDuckURL":
        from .database import MotherDuckURL

        return MotherDuckURL
    if name == "SnowflakeURL":
        from .database import SnowflakeURL

        return SnowflakeURL
    if name == "create_tpch_example_duckdb_db":
        from .utils.example_data import create_tpch_example_duckdb_db

        return create_tpch_example_duckdb_db
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
