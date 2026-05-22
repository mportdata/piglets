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
from .capabilities.search_space_finalization import (
    GlobalSynthesizer as GlobalSynthesizer,
    SearchSpaceFinalizer as SearchSpaceFinalizer,
)
from .capabilities.search_space_grounding import (
    SearchSpaceGrounder as SearchSpaceGrounder,
    SemanticLinker as SemanticLinker,
)
from .capabilities.search_space_reduction import (
    DualPathwayPruner as DualPathwayPruner,
    SearchSpaceReducer as SearchSpaceReducer,
)
from .capabilities.search_space_verification import (
    ParallelDataProfiler as ParallelDataProfiler,
    SearchSpaceVerifier as SearchSpaceVerifier,
)
from .policies import RuleMode as RuleMode
from .policies import SemanticRules as SemanticRules
from .workflows import (
    EnterUserQuestion as EnterUserQuestion,
    FinalizeSearchSpace as FinalizeSearchSpace,
    GenerateHypothesis as GenerateHypothesis,
    GroundSearchSpace as GroundSearchSpace,
    LoadSearchSpace as LoadSearchSpace,
    ReduceSearchSpace as ReduceSearchSpace,
    VerifySearchSpace as VerifySearchSpace,
    WorkflowRunner as WorkflowRunner,
    WorkflowStage as WorkflowStage,
)
from .types import (
    AggregatePlan as AggregatePlan,
    ColumnSchema as ColumnSchema,
    DatabaseSemanticAnnotation as DatabaseSemanticAnnotation,
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
    TableSemanticAnnotation as TableSemanticAnnotation,
    TableSchema as TableSchema,
    WorkflowState as WorkflowState,
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
    # Search space grounding
    "GroundSearchSpace",
    "SearchSpaceGrounder",
    "SemanticLinker",
    # Search space reduction
    "DualPathwayPruner",
    "SearchSpaceReducer",
    # Search space verification
    "ParallelDataProfiler",
    "SearchSpaceVerifier",
    "VerifySearchSpace",
    # Search space finalization
    "EnterUserQuestion",
    "FinalizeSearchSpace",
    "GlobalSynthesizer",
    "SearchSpaceFinalizer",
    "RuleMode",
    "SemanticRules",
    "GenerateHypothesis",
    "LoadSearchSpace",
    "ReduceSearchSpace",
    "WorkflowRunner",
    "WorkflowStage",
    # Types
    "AggregatePlan",
    "ColumnSchema",
    "DatabaseSemanticAnnotation",
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
    "TableSemanticAnnotation",
    "TableSchema",
    "WorkflowState",
    # Profiling
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
