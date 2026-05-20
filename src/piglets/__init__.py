from .database import (
    BigQueryURL as BigQueryURL,
    DatabaseConnector as DatabaseConnector,
    URL as URL,
    database_name_from_connection as database_name_from_connection,
    database_name_from_connection_string as database_name_from_connection_string,
    database_type_from_connection as database_type_from_connection,
)
from .capabilities.hypothesis_generation import (
    HypothesisGenerator as HypothesisGenerator,
    LogicalPlanner as LogicalPlanner,
)
from .policies import RuleMode as RuleMode
from .policies import SemanticRules as SemanticRules
from .profiling import Profiler as Profiler
from .pruning import Pruner as Pruner
from .semantic_linking import SemanticLinker as SemanticLinker
from .synthesizing import Synthesizer as Synthesizer
from .workflows import (
    GenerateHypothesis as GenerateHypothesis,
    LoadSearchSpace as LoadSearchSpace,
    WorkflowRunner as WorkflowRunner,
    WorkflowStage as WorkflowStage,
)
from .types import (
    AggregatePlan as AggregatePlan,
    ColumnSchema as ColumnSchema,
    DatabaseSchema as DatabaseSchema,
    DatabaseProfileResult as DatabaseProfileResult,
    DeletionColumns as DeletionColumns,
    DeletionSet as DeletionSet,
    Hypothesis as Hypothesis,
    LogicalPlan as LogicalPlan,
    LogicalPlans as LogicalPlans,
    LogicalSteps as LogicalSteps,
    Question as Question,
    SearchSpace as SearchSpace,
    PreservationColumns as PreservationColumns,
    PreservationSet as PreservationSet,
    ProfilingQuery as ProfilingQuery,
    ProfilingQueries as ProfilingQueries,
    QueryResult as QueryResult,
    QueryResults as QueryResults,
    PruningColumns as PruningColumns,
    RefinedSchemaColumn as RefinedSchemaColumn,
    RefinedSchemaTable as RefinedSchemaTable,
    RejectedCandidate as RejectedCandidate,
    SemanticLinkingResult as SemanticLinkingResult,
    SQLQueries as SQLQueries,
    SQLQuery as SQLQuery,
    SynthesisRound as SynthesisRound,
    SynthesisResult as SynthesisResult,
    SynthesisRunResult as SynthesisRunResult,
    TableProfileColumnResult as TableProfileColumnResult,
    TableProfileResult as TableProfileResult,
    TableSchema as TableSchema,
    WorkflowContext as WorkflowContext,
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
    "HypothesisGenerator",
    "LogicalPlanner",
    "SemanticLinker",
    "RuleMode",
    "SemanticRules",
    "GenerateHypothesis",
    "LoadSearchSpace",
    "WorkflowRunner",
    "WorkflowStage",
    # Types
    "AggregatePlan",
    "ColumnSchema",
    "DatabaseSchema",
    "DatabaseProfileResult",
    "DeletionColumns",
    "DeletionSet",
    "Hypothesis",
    "LogicalPlan",
    "LogicalPlans",
    "LogicalSteps",
    "Question",
    "SearchSpace",
    "PreservationColumns",
    "PreservationSet",
    "PruningColumns",
    "QueryResult",
    "QueryResults",
    "RefinedSchemaColumn",
    "RefinedSchemaTable",
    "RejectedCandidate",
    "SemanticLinkingResult",
    "SQLQueries",
    "SQLQuery",
    "SynthesisRound",
    "SynthesisResult",
    "SynthesisRunResult",
    "TableProfileColumnResult",
    "TableProfileResult",
    "TableSchema",
    "WorkflowContext",
    # Pruning
    "Pruner",
    # Profiling
    "Profiler",
    "ProfilingQuery",
    "ProfilingQueries",
    # Synthesizing
    "Synthesizer"
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
