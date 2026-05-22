from concurrent.futures import ThreadPoolExecutor
import logging

from langchain.chat_models import init_chat_model

from piglets.database import DatabaseConnector
from piglets.policies import SemanticRules
from piglets.types import (
    DatabaseProfileResult,
    ProfilingQueries,
    ProfilingQuery,
    Question,
    QueryResult,
    QueryResults,
    SearchSpace,
    SemanticLinkingResult,
    TableSchema,
    TableProfileResult,
    WorkflowState,
)

logger = logging.getLogger(__name__)


def _database_schema_from_search_space(search_space: SearchSpace):
    if search_space.database_schema is None:
        raise ValueError("search_space must contain a database_schema")
    return search_space.database_schema


class ParallelDataProfiler:
    def __init__(
        self,
        model_name: str,
        database_connector: DatabaseConnector | None = None,
        search_space: SearchSpace | None = None,
        model_provider: str = None,
        rules: SemanticRules | None = None,
        max_query_repair_attempts: int = 1,
    ):
        if max_query_repair_attempts < 0:
            raise ValueError(
                "max_query_repair_attempts must be greater than or equal to 0"
            )

        self.model_name = model_name
        self.database_connector = database_connector
        self.search_space = search_space
        self.model_provider = model_provider
        self.rules = rules or SemanticRules()
        self.max_query_repair_attempts = max_query_repair_attempts

    @property
    def database_schema(self):
        if self.search_space is None:
            raise ValueError("search_space must be set before profiling")
        return _database_schema_from_search_space(self.search_space)

    def verify(self, state: WorkflowState) -> WorkflowState:
        """Verify the current search space by profiling table content."""
        if self.database_connector is None:
            raise ValueError("database_connector must be set before verification")

        database_profile_result = self.profile_database(
            search_space=state.search_space,
            database_connector=self.database_connector,
            question=state.question,
            semantic_linking_result=state.search_space.semantic_linking_result,
        )
        verified_search_space = state.search_space.model_copy(
            update={"database_profile_result": database_profile_result}
        )
        return state.model_copy(update={"search_space": verified_search_space})

    def _generate_table_profiler_queries(
        self,
        question: Question,
        table_schema: TableSchema,
        semantic_linking_result: SemanticLinkingResult | None = None,
    ) -> ProfilingQueries:
        logger.debug("Generating profiling queries for table %s", table_schema.name)
        natural_language_question = question.natural_language_question

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(ProfilingQueries)
        critical_rules = self.rules.critical_rules_to_string()
        sql_type = f"{self.database_schema.database_type.upper()} SQL"
        semantic_table_functions_lower = (
            {k.lower(): v for k, v in semantic_linking_result.table_functions.items()}
            if semantic_linking_result
            else {}
        )
        semantic_table_function = semantic_table_functions_lower.get(
            table_schema.name.lower(),
            "Unknown Role",
        )

        # TODO: Include column descriptions here once ColumnSchema supports them.
        DATA_PROFILE_QUERY_GENERATION_PROMPT = f"""
            *** TASK CONTEXT ***
            You are an agent exploring a database table to verify its
            relevance to a user question.
            You must not explore randomly. You must verify if this
            table fits its anticipated role.
            {critical_rules}

            *** TARGET TABLE: {table_schema.name} ***
            Columns:
            {table_schema.columns_to_string()}

            *** USER QUESTION ***
            {natural_language_question}

            *** ANTICIPATED ROLE ***
            This table was identified as: {semantic_table_function}. Use this to
            guide your exploration.

            *** YOUR MISSION ***
            Generate 3-8 {sql_type} queries to investigate. **Focus on
            understanding the table’s semantics and utility.**
            Each query must profile only the target table, {table_schema.name}.
            Do not join to, reference, or infer data from any other table.

            **Motivation for Exploration**:
            1. **Semantic Alignment**: Check distinct values to understand what the column *means* versus what the query
            *needs*. (e.g., If column is ’type’, does it contain the specific
            categories? If ’status’, does it contain values like ’Active’
            or code ’1’?)
            2. **Granularity & Scope**: Verify the table’s grain (e.g., is
            it one row per Order or per Item?). This determines if it
            supports the required aggregations.
            3. **Bridge/Connectivity**: If this looks like a linking table,
            verify the Foreign Keys are populated (not all NULL) to
            ensure it can actually serve as a bridge.
            4. **Data Quality**: Are critical columns (targets for filters
            or answers) usable, or are they mostly NULL?

            *** OUTPUT FORMAT ***
            Return structured data matching the ProfilingQueries schema:
            - query: a list of 3-8 objects.
            - Each object must contain:
              - motivation: a concise reason for running the profiling query.
              - query: the {sql_type} query string.

            Do not wrap queries in markdown fences. Put the reason for each
            query in the motivation field, not in SQL comments.
            Generate your exploration queries:
        """

        profiling_queries = llm.invoke(DATA_PROFILE_QUERY_GENERATION_PROMPT)
        logger.debug(
            "Generated %s profiling queries for table %s",
            len(profiling_queries.query),
            table_schema.name,
        )

        return profiling_queries

    @staticmethod
    def _execute_indexed_profiling_query(
        database_connector: DatabaseConnector,
        indexed_query: tuple[int, ProfilingQuery],
    ) -> tuple[int, ProfilingQuery, QueryResult | None, Exception | None]:
        index, query = indexed_query
        try:
            query_result = database_connector.execute_query(query)
        except Exception as error:
            return index, query, None, error

        return index, query, query_result, None

    def _repair_profiling_query(
        self,
        question: Question,
        table_schema: TableSchema,
        failed_query: ProfilingQuery,
        error: Exception,
    ) -> ProfilingQuery:
        logger.debug("Repairing profiling query for table %s", table_schema.name)
        natural_language_question = question.natural_language_question
        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(ProfilingQuery)
        sql_type = f"{self.database_schema.database_type.upper()} SQL"

        QUERY_REPAIR_PROMPT = f"""
            *** TASK CONTEXT ***
            A generated profiling query failed during execution. Repair the
            SQL while preserving the original profiling intent.

            *** SQL DIALECT ***
            {sql_type}

            *** TARGET TABLE: {table_schema.name} ***
            Columns:
            {table_schema.columns_to_string()}

            *** USER QUESTION ***
            {natural_language_question}

            *** ORIGINAL MOTIVATION ***
            {failed_query.motivation}

            *** FAILED QUERY ***
            {failed_query.query}

            *** DATABASE ERROR ***
            {type(error).__name__}: {error}

            *** REPAIR RULES ***
            Return exactly one valid {sql_type} query.
            The query must profile only the target table, {table_schema.name}.
            Do not join to, reference, or infer data from any other table.
            Use only columns listed in the target table schema.
            Preserve the original motivation unless it is no longer accurate.
            Do not wrap the query in markdown fences.

            *** OUTPUT FORMAT ***
            Return structured data matching the ProfilingQuery schema:
            - motivation: a concise reason for running the repaired query.
            - query: the repaired {sql_type} query string.
        """

        return llm.invoke(QUERY_REPAIR_PROMPT)

    def _execute_table_profiling_queries(
        self,
        database_connector: DatabaseConnector,
        profiling_queries: ProfilingQueries,
        question: Question,
        table_schema: TableSchema,
    ) -> QueryResults:
        queries = list(profiling_queries.query)
        if not queries:
            logger.debug("No profiling queries to execute")
            return QueryResults()

        query_results: list[QueryResult | None] = [None] * len(queries)
        pending_queries = list(enumerate(queries))
        repair_attempt = 0
        logger.debug(
            "Executing %s profiling queries with %s workers",
            len(queries),
            min(len(queries), 8),
        )

        while pending_queries:
            max_workers = min(len(pending_queries), 8)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                executions = list(
                    executor.map(
                        lambda indexed_query: self._execute_indexed_profiling_query(
                            database_connector,
                            indexed_query,
                        ),
                        pending_queries,
                    )
                )

            failed_queries: list[tuple[int, ProfilingQuery, Exception]] = []
            for index, query, query_result, error in executions:
                if error is None and query_result is not None:
                    query_results[index] = query_result
                elif error is not None:
                    failed_queries.append((index, query, error))

            if not failed_queries:
                break

            if repair_attempt >= self.max_query_repair_attempts:
                logger.error(
                    "Failed to execute profiling query for table %s after %s repair attempts: %s",
                    table_schema.name,
                    repair_attempt,
                    type(failed_queries[0][2]).__name__,
                )
                raise failed_queries[0][2]

            repair_attempt += 1
            logger.warning(
                "Repairing %s failed profiling queries for table %s, attempt %s of %s",
                len(failed_queries),
                table_schema.name,
                repair_attempt,
                self.max_query_repair_attempts,
            )
            pending_queries = [
                (
                    index,
                    self._repair_profiling_query(
                        question=question,
                        table_schema=table_schema,
                        failed_query=query,
                        error=error,
                    ),
                )
                for index, query, error in failed_queries
            ]

        executed_query_results = [
            query_result
            for query_result in query_results
            if query_result is not None
        ]
        if len(executed_query_results) != len(queries):
            raise RuntimeError(
                "Profiling query execution completed with missing results"
            )

        logger.debug("Executed %s profiling queries", len(executed_query_results))

        return QueryResults(query_results=executed_query_results)

    def _profile_table_from_query_results(
        self,
        question: Question,
        query_results: QueryResults,
        table_schema: TableSchema,
    ) -> TableProfileResult:
        logger.debug("Profiling table %s from query results", table_schema.name)
        natural_language_question = question.natural_language_question
        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(TableProfileResult)

        TABLE_PROFILE_PROMPT = f"""
            *** TASK ***
            Based on the exploration history and results above,
            determine if table {table_schema.name} is RELEVANT to the User
            Question.
            *** EXPLORATION EVIDENCE ***
            {query_results.to_string()}
            *** USER QUESTION ***
            {natural_language_question}
            *** DECISION GUIDELINES ***
            - **Direct Match**: Contains the specific answer data.
            - **Bridge Table**: Contains IDs needed to join other relevant tables (CRITICAL: Keep even if no other useful data).
            - **Filter Source**: Contains columns needed to restrict the
            result.
            - **Calculation Support**: Contains numerical columns
            needed for aggregation (e.g., score for AVG, price for
            SUM).
            *** OUTPUT GUIDELINES ***
            - table_name: The exact target table name, {table_schema.name}.
            - relevant: Whether this table is relevant to the user question.
            - relevant_columns: Columns relevant to the user question.
            - column_name: The relevant column name.
            - relevance_reason: Explain the column's logical role.
            - observations: Summarize factual findings from exploration.
            - table_summary: A concise summary of what this table
            represents in the context of the query.
            *** OUTPUT FORMAT ***
            Return structured data matching the TableProfileResult schema:
            - table_name: string.
            - relevant: boolean.
            - relevant_columns: list of TableProfileColumnResult objects.
            - Each relevant_columns item must contain:
              - column_name: string.
              - relevance_reason: string.
              - observations: string.
            - table_summary: string.

            Example shape:
            ```json
                {{
                    "table_name": "{table_schema.name}",
                    "relevant": true,
                    "relevant_columns": [
                        {{
                            "column_name": "name",
                            "relevance_reason": "...",
                            "observations": "..."
                        }}
                    ],
                    "table_summary": "..."
                }}
            ```
            Provide your analysis:
        """
        
        table_profile_result = llm.invoke(TABLE_PROFILE_PROMPT)
        table_profile_result.table_name = table_schema.name
        logger.debug(
            "Profiled table %s from query results: relevant=%s, relevant_columns=%s",
            table_schema.name,
            table_profile_result.relevant,
            len(table_profile_result.relevant_columns),
        )

        return table_profile_result
    
    def profile_table(
            self,
            question: Question,
            table_schema: TableSchema,
            database_connector: DatabaseConnector,
            semantic_linking_result: SemanticLinkingResult | None = None,
    ) -> TableProfileResult:
        logger.info("Profiling table %s", table_schema.name)
        profiling_queries = self._generate_table_profiler_queries(
            question=question,
            table_schema=table_schema,
            semantic_linking_result=semantic_linking_result,
        )
        query_results = self._execute_table_profiling_queries(
            database_connector=database_connector,
            profiling_queries=profiling_queries,
            question=question,
            table_schema=table_schema,
        )
        table_profile_result = self._profile_table_from_query_results(
            question=question,
            query_results=query_results,
            table_schema=table_schema,
        )
        logger.info(
            "Profiled table %s: relevant=%s, relevant_columns=%s",
            table_schema.name,
            table_profile_result.relevant,
            len(table_profile_result.relevant_columns),
        )
        return table_profile_result

    def profile_database(
        self,
        search_space: SearchSpace,
        database_connector: DatabaseConnector | None,
        question: Question,
        semantic_linking_result: SemanticLinkingResult | None = None
    ) -> DatabaseProfileResult:
        if database_connector is None:
            if self.database_connector is None:
                raise ValueError("database_connector must be provided")
            database_connector = self.database_connector

        self.search_space = search_space
        database_schema = _database_schema_from_search_space(search_space)
        logger.info(
            "Profiling database %s with %s tables",
            database_schema.name,
            len(database_schema.table_schemas),
        )
        database_profile_result = DatabaseProfileResult(
            database_type=database_schema.database_type,
            database_name=database_schema.name,
        )
        table_schemas = list(database_schema.table_schemas)
        if not table_schemas:
            logger.info("Profiled database %s with 0 table profiles", database_schema.name)
            return database_profile_result

        max_workers = min(len(table_schemas), 4)
        logger.debug(
            "Profiling %s database tables with %s workers",
            len(table_schemas),
            max_workers,
        )

        def profile_table(table_schema: TableSchema) -> TableProfileResult:
            return self.profile_table(
                question=question,
                table_schema=table_schema,
                database_connector=database_connector,
                semantic_linking_result=semantic_linking_result,
            )

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                table_profile_results = list(executor.map(profile_table, table_schemas))
        except Exception:
            logger.exception("Failed to profile database %s", database_schema.name)
            raise

        database_profile_result.table_profile_results.extend(table_profile_results)
        logger.info(
            "Profiled database %s with %s table profiles",
            database_schema.name,
            len(database_profile_result.table_profile_results),
        )
        return database_profile_result
