from langchain.chat_models import init_chat_model

from piglets.policies import SemanticRules
from piglets.types import (
    ProfilingQueries,
    SemanticLinkingResult,
    Table,
)


class Profiler():
    def __init__(
        self,
        model_name: str,
        model_provider: str = None,
        rules: SemanticRules | None = None,
    ):
        self.model_name = model_name
        self.model_provider = model_provider
        self.rules = rules or SemanticRules()

    def profile_table(
        self,
        natural_language_query: str,
        database_type: str | None,
        table: Table,
        semantic_linking_result: SemanticLinkingResult,
    ) -> ProfilingQueries:

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(ProfilingQueries)
        critical_rules = self.rules.critical_rules_to_string()
        sql_type = f"{database_type.upper()} SQL" if database_type else "SQL"
        semantic_table_functions_lower = {k.lower(): v for k, v in semantic_linking_result.table_functions.items()}
        semantic_table_function = semantic_table_functions_lower.get(table.name.lower(), "Unknown Role")

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
            - exploratory_queries: a list of 3-8 objects.
            - Each object must contain:
              - motivation: a concise reason for running the profiling query.
              - query: the {sql_type} query string.

            Do not wrap queries in markdown fences. Put the reason for each
            query in the motivation field, not in SQL comments.
            Generate your exploration queries:
        """

        profiling_queries = llm.invoke(DATA_PROFILE_QUERY_GENERATION_PROMPT)

        return profiling_queries
