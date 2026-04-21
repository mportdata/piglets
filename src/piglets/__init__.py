from .database import (
    BigQueryURL as BigQueryURL,
    DatabaseConnector as DatabaseConnector,
    URL as URL,
    database_name_from_connection as database_name_from_connection,
    database_name_from_connection_string as database_name_from_connection_string,
)
from .planning import LogicalPlanner as LogicalPlanner
from .pruning import Pruner as Pruner
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
    PruningColumns as PruningColumns,
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
    # Planning
    "LogicalPlanner",
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
    "Table",
    # Pruning
    "Pruner"
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
