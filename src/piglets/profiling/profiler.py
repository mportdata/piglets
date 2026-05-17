from langchain.chat_models import init_chat_model

from piglets.database import DatabaseConnector
from piglets.policies import SemanticRules
from piglets.types import (
    Database,
    ProfilingQueries,
    QueryResult,
    QueryResults,
    SemanticLinkingResult,
    Table,
    TableProfileResult,
)

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

        return profiling_queries

    # TODO: Parallel query execution
    def _execute_table_profiling_queries(
        self,
        database_connector: DatabaseConnector,
        profiling_queries: ProfilingQueries,  
    ) -> QueryResults:
        query_results = QueryResults()
        for profiling_query in profiling_queries.query:
            query_result: QueryResult = database_connector.execute_query(profiling_query)
            query_results.query_results.append(query_result)
        return query_results

    def _profile_table_from_query_results(
        self,
        natural_language_query: str,
        query_results: QueryResults,
        table: Table,
    ) -> TableProfileResult:
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

        return table_profile_result
    
    def profile_table(
            self,
            natural_language_query: str,
            table: Table,
            database_connector: DatabaseConnector,
            semantic_linking_result: SemanticLinkingResult | None = None,
    ) -> TableProfileResult:
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
        return table_profile_result
    
    #TODO profile self.database by profiling all of it's tables in parallel
    # returning a list of TableProfileResults
    #def profile_database(self) -> DatabaseProfileResult:

