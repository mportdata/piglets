from langchain.chat_models import init_chat_model

from piglets.types import AggregatePlan, Database, LogicalPlan, SemanticLinkingResult

class SemanticLinker:
    def __init__(
        self,
        model_name: str,
        model_provider: str = None,
    ):
        self.model_name = model_name
        self.model_provider = model_provider
    
    def link(
        self,
        natural_language_query: str,
        database: Database,
        logical_plan: LogicalPlan | AggregatePlan = None,
    ) -> SemanticLinkingResult:
    
        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(
            SemanticLinkingResult,
            method="function_calling",
        )

        SEMANTIC_LINKING_PROMPT = f"""
            *** TASK CONTEXT ***
            You are a Senior Data Architect. You have full visibility of
            the database schema and a user question.
            Your goal is to perform **Semantic Linking**: Analyze the
            database structure and how it grounds the user’s intent.
            *** USER QUESTION ***
            {natural_language_query}
            *** Logical Plan ***
            {logical_plan}
            *** DATABASE SCHEMA ***
            {database.export_as_string()}
            *** YOUR TASKS ***
            1. **Database Structure Overview**: Describe the database
            structure in detail (e.g., ’A banking system with customers
            and transactions...’).
            2. **Query-Specific Content Analysis**: Analyze the query
            against the available columns. Identify which columns are
            likely targets, filters, or join keys.
            3. **Table Functional Analysis**: For EVERY potentially
            relevant table, describe its specific function regarding this
            query.
            - Is it a **Target Table**? (Contains the answer columns)
            - Is it a **Bridge Table**? (Doesn’t have semantic data
            but is needed to join Table A and Table B via Foreign Keys)
            - Is it a **Filtering Table**? (Contains columns for
            WHERE clauses)
            - **CRITICAL**: A table may have multiple roles. If a
            table is needed as a BRIDGE, you MUST explicitly state
            that it connects Entity X and Entity Y, even if it looks
            empty of content.
            *** OUTPUT FORMAT ***
            You MUST return all top-level fields: database_structure,
            query_specific_content_analysis, and table_functions. If no
            table function can be established from the schema, return
            an empty table_functions object.
            {{
            "database_structure": "Database structure overview...",
            "query_specific_content_analysis": "Detailed mapping
            of query terms to DB columns/logic...",
            "table_functions": {{
            "table_name_1": "Acts as a bridge table connecting
            Students and Classes via student_id and class_id.",
            "table_name_2": "Contains the ’score’ column needed
            for calculation and ’exam_date’ for filtering."
            }}
            }}
        """

        semantic_linking_result = llm.invoke(SEMANTIC_LINKING_PROMPT)

        return semantic_linking_result
