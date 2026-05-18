from concurrent.futures import ThreadPoolExecutor
import logging

from langchain.chat_models import init_chat_model

from piglets.database import DatabaseConnector
from piglets.policies import SemanticRules
from piglets.types import (
    Database,
    DatabaseProfileResult,
    ProfilingQueries,
    QueryResults,
    SemanticLinkingResult,
    Table,
    TableProfileResult,
)

logger = logging.getLogger(__name__)


class Profiler():
    def __init__(
        self,
        model_name: str,
        database: Database,
        model_provider: str = None,
        rules: SemanticRules | None = None,
    ):
        self.model_name = model_name
        self.database = database
        self.model_provider = model_provider
        self.rules = rules or SemanticRules()

    def _generate_table_profiler_queries(
        self,
        natural_language_query: str,
        table: Table,
        semantic_linking_result: SemanticLinkingResult | None = None,
    ) -> ProfilingQueries:
        logger.debug("Generating profiling queries for table %s", table.name)

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(ProfilingQueries)
        critical_rules = self.rules.critical_rules_to_string()
        sql_type = f"{self.database.database_type.upper()} SQL"
        semantic_table_functions_lower = (
            {k.lower(): v for k, v in semantic_linking_result.table_functions.items()}
            if semantic_linking_result
            else {}
        )
        semantic_table_function = semantic_table_functions_lower.get(
            table.name.lower(),
            "Unknown Role",
        )

        # TODO: Include column descriptions here once Column supports them.
        DATA_PROFILE_QUERY_GENERATION_PROMPT = f"""
            *** TASK CONTEXT ***
            You are an agent exploring a database table to verify its
            relevance to a user question.
            You must not explore randomly. You must verify if this
            table fits its anticipated role.
            {critical_rules}

            *** TARGET TABLE: {table.name} ***
            Columns:
            {table.columns_to_string()}

            *** USER QUESTION ***
            {natural_language_query}

            *** ANTICIPATED ROLE ***
            This table was identified as: {semantic_table_function}. Use this to
            guide your exploration.

            *** YOUR MISSION ***
            Generate 3-8 {sql_type} queries to investigate. **Focus on
            understanding the table’s semantics and utility.**
            Each query must profile only the target table, {table.name}.
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
            table.name,
        )

        return profiling_queries

    def _execute_table_profiling_queries(
        self,
        database_connector: DatabaseConnector,
        profiling_queries: ProfilingQueries,  
    ) -> QueryResults:
        queries = list(profiling_queries.query)
        if not queries:
            logger.debug("No profiling queries to execute")
            return QueryResults()

        max_workers = min(len(queries), 8)
        logger.debug(
            "Executing %s profiling queries with %s workers",
            len(queries),
            max_workers,
        )
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                query_results = list(executor.map(database_connector.execute_query, queries))
        except Exception:
            logger.exception("Failed to execute profiling queries")
            raise

        logger.debug("Executed %s profiling queries", len(query_results))

        return QueryResults(query_results=query_results)

    def _profile_table_from_query_results(
        self,
        natural_language_query: str,
        query_results: QueryResults,
        table: Table,
    ) -> TableProfileResult:
        logger.debug("Profiling table %s from query results", table.name)
        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(TableProfileResult)

        TABLE_PROFILE_PROMPT = f"""
            *** TASK ***
            Based on the exploration history and results above,
            determine if table {table.name} is RELEVANT to the User
            Question.
            *** EXPLORATION EVIDENCE ***
            {query_results.to_string()}
            *** USER QUESTION ***
            {natural_language_query}
            *** DECISION GUIDELINES ***
            - **Direct Match**: Contains the specific answer data.
            - **Bridge Table**: Contains IDs needed to join other relevant tables (CRITICAL: Keep even if no other useful data).
            - **Filter Source**: Contains columns needed to restrict the
            result.
            - **Calculation Support**: Contains numerical columns
            needed for aggregation (e.g., score for AVG, price for
            SUM).
            *** OUTPUT GUIDELINES ***
            - relevant: Whether this table is relevant to the user question.
            - relevant_columns: Columns relevant to the user question.
            - column_name: The relevant column name.
            - relevance_reason: Explain the column's logical role.
            - observations: Summarize factual findings from exploration.
            - table_summary: A concise summary of what this table
            represents in the context of the query.
            *** OUTPUT FORMAT ***
            Return structured data matching the TableProfileResult schema:
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
        logger.debug(
            "Profiled table %s from query results: relevant=%s, relevant_columns=%s",
            table.name,
            table_profile_result.relevant,
            len(table_profile_result.relevant_columns),
        )

        return table_profile_result
    
    def profile_table(
            self,
            natural_language_query: str,
            table: Table,
            database_connector: DatabaseConnector,
            semantic_linking_result: SemanticLinkingResult | None = None,
    ) -> TableProfileResult:
        logger.info("Profiling table %s", table.name)
        profiling_queries = self._generate_table_profiler_queries(
            natural_language_query=natural_language_query,
            table=table,
            semantic_linking_result=semantic_linking_result,
        )
        query_results = self._execute_table_profiling_queries(
            database_connector=database_connector,
            profiling_queries=profiling_queries, 
        )
        table_profile_result = self._profile_table_from_query_results(
            natural_language_query=natural_language_query,
            query_results=query_results,
            table=table,
        )
        logger.info(
            "Profiled table %s: relevant=%s, relevant_columns=%s",
            table.name,
            table_profile_result.relevant,
            len(table_profile_result.relevant_columns),
        )
        return table_profile_result

    def profile_database(
        self,
        database: Database,
        database_connector: DatabaseConnector,
        natural_language_query: str,
        semantic_linking_result: SemanticLinkingResult | None = None
    ) -> DatabaseProfileResult:
        logger.info(
            "Profiling database %s with %s tables",
            database.name,
            len(database.tables),
        )
        database_profile_result = DatabaseProfileResult(
            database_type=database.database_type,
            database_name=database.name,
        )
        tables = list(database.tables)
        if not tables:
            logger.info("Profiled database %s with 0 table profiles", database.name)
            return database_profile_result

        max_workers = min(len(tables), 4)
        logger.debug(
            "Profiling %s database tables with %s workers",
            len(tables),
            max_workers,
        )

        def profile_table(table: Table) -> TableProfileResult:
            return self.profile_table(
                natural_language_query=natural_language_query,
                table=table,
                database_connector=database_connector,
                semantic_linking_result=semantic_linking_result,
            )

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                table_profile_results = list(executor.map(profile_table, tables))
        except Exception:
            logger.exception("Failed to profile database %s", database.name)
            raise

        database_profile_result.table_profile_results.extend(table_profile_results)
        logger.info(
            "Profiled database %s with %s table profiles",
            database.name,
            len(database_profile_result.table_profile_results),
        )
        return database_profile_result
