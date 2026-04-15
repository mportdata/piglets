from langchain.chat_models import init_chat_model

from piglets.types import AggregatePlan, Database, DeletionSet, LogicalPlan, PreservationSet


class Pruner():
    def __init__(self, model_name: str, model_provider: str = None):
        self.model_name = model_name
        self.model_provider = model_provider

    def get_tables_and_fields_to_preserve(self, natural_language_query: str, database: Database, logical_plan: LogicalPlan | AggregatePlan = None) -> PreservationSet:

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(PreservationSet)

        PRESERVATION_SET_PROMPT = f"""
            *** TASK CONTEXT ***
            You are a Lead Data Architect. You have a Logical Plan to
            answer a query.
            Your task: **Positive Selection**. Identify database tables
            or columns that are **RELEVANT** or **NECESSARY** to
            the plan.
            *** USER QUESTION ***
            {natural_language_query}
            {f"*** MASTER LOGICAL PLAN ***\n{logical_plan.export_as_string()}" if logical_plan else ""}
            *** FULL DATABASE SCHEMA ***
            {database.export_as_string()}
            *** STRICT GUIDELINES ***
            1. **High Recall (Safety)**: Select ALL columns that might
            be useful for joining, filtering, grouping, or returning results. If you are not sure about the relevance of a column,
            e.g., the name and the description are ambiguous, **PICK
            IT**.
            2. **Definition of Relevance**: Relevance includes both
            **Lexical Matching** and **Semantic Relatedness** over
            column name and description.
            - **Lexical**: If a word from the query appears in the table or column name (e.g., query mentions "school" -> keep
            ‘school_code‘, ‘school_type‘, etc.), it MUST be selected.
            - **Semantic**: Identify columns conceptually related to
            the topic. For example, if the query asks about "patents that
            were granted in ...", then the column ‘grant_date‘ should
            be kept.
            - **Discriminators**: ALWAYS select primary keys and
            common identifiers (‘xxx_id‘, ‘xxx_code‘, ‘xxx_name‘) for
            relevant tables, as they are needed for joins.
            3. **Output Selection List**:
            - **Tables**: If a whole table is relevant, list it in ‘relevant_tables‘.
            - **Columns**: List specific useful columns in ‘relevant_columns‘. If a table is already listed in ‘relevant_tables‘, the columns can be omitted.
            4. **Grouped Tables**: If multiple tables are presented as
            sharing the same columns, you MUST list the selection
            instructions for **EACH** table explicitly. Pay close
            attention to name differences within the group (e.g.,
            xx_2017 vs xx_2026), as these reflect specific data dimensions (like time) that determine relevance to the query.
            *** OUTPUT FORMAT ***
            ```json
            {{
            "relevant_tables": ["table_useful_1"],
            "relevant_columns": [
            {{
            "table": "t1",
            "columns": ["col_useful_1", "col_pk_id"]
            }}
            ]
            }}
            ```
        """

        preservation_set = llm.invoke(PRESERVATION_SET_PROMPT)

        return preservation_set

    def get_tables_and_fields_to_delete(self, natural_language_query: str, database: Database, logical_plan: LogicalPlan | AggregatePlan = None) -> DeletionSet:

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(DeletionSet)

        DELETION_SET_PROMPT = f"""
            *** TASK CONTEXT ***
            You are a Lead Data Architect. You have a Logical Plan to
            answer a query.
            Your task: **Negative Pruning**. Identify database tables or columns that are **100% IRRELEVANT** to the plan.
            *** USER QUESTION ***
            {natural_language_query}
            {f"*** MASTER LOGICAL PLAN ***\n{logical_plan.export_as_string()}" if logical_plan else ""}
            *** FULL DATABASE SCHEMA ***
            {database.export_as_string()}
            *** STRICT GUIDELINES ***
            1. **High Recall (Safety)**:
            - If the column name is related to the query (even 1%
            chance), you should keep it. If not, check the desciption to
            see if it is related to the query. Sometimes the description is
            not clear, then you should pay close attention to the sample
            rows of the table. If the sample values of some columns
            are related to the query, you should keep these columns. If
            all of these information are not clear enough, remove it.
            2. **Definition of Relevance**: Relevance includes both
            **Lexical Matching** and **Semantic Relatedness** over
            column name and description.
            - **Lexical**: If a word from the query appears in the
            name (e.g., query mentions "school" -> keep ‘school_code‘,
            ‘school_type‘, etc.), it MUST be retained.
            - **Semantic**: Keep columns conceptually related to
            the topic. For example, if the query asks about "patents that
            were granted in ...", then the column ‘grant_date‘ should
            be kept.
            - **CRITICAL**: Do NOT remove discriminator columns
            such as ‘xxx_id‘, ‘xxx_name‘, ‘xxx_code‘, or ‘xxx_type‘ if
            the table itself is kept.
            3. **Output Removal List**:
            - **Tables**: If a whole table is irrelevant, list it in ‘obviously_irrelevant_tables‘. Then all columns of that table will
            be kept. You do NOT need to list its columns separately.
            - **Columns**: If specific columns of a table are noise,
            list them in ‘obviously_irrelevant_columns‘.
            4. **Grouped Tables**: If multiple tables are presented as
            sharing the same columns, you MUST list the removal
            instructions for **EACH** table explicitly. Pay close
            attention to name differences within the group (e.g.,
            xx_2017 vs xx_2026), as these reflect specific data dimensions (like time) that determine relevance to the query.
            *** OUTPUT FORMAT ***
            ```json
            {{
            "obviously_irrelevant_tables": ["table_unused_1", "table_unused_2"],
            "obviously_irrelevant_columns": [
            {{
            "table": "t1",
            "columns": ["col_unused_1", "col_unused_2"]
            }}
            ]
            }}
            ```
        """

        deletion_set = llm.invoke(DELETION_SET_PROMPT)

        return deletion_set
    
    def dual_pathway_pruning(self, natural_language_query: str, database: Database, logical_plan: LogicalPlan | AggregatePlan = None) -> Database:
        """Run both the preservation and deletion pathways to prune the database schema, then combine the results to produce a final pruned database."""
        
        preservation_set = self.get_tables_and_fields_to_preserve(
            natural_language_query=natural_language_query,
            database=database,
            logical_plan=logical_plan
        )
        
        deletion_set = self.get_tables_and_fields_to_delete(
            natural_language_query=natural_language_query,
            database=database,
            logical_plan=logical_plan
        )

        database_without_deletion_set = database.subtract(deletion_set.to_database_type(database))
        final_pruned_database = database_without_deletion_set.union(preservation_set.to_database_type(database))
        
        return final_pruned_database
