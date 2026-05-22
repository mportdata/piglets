from langchain.chat_models import init_chat_model

from piglets.policies import SemanticRules
from piglets.types import (
    DatabaseSemanticAnnotation,
    Hypothesis,
    Question,
    SearchSpace,
    SemanticLinkingResult,
    TableSemanticAnnotation,
    WorkflowState,
)


def _database_schema_from_search_space(search_space: SearchSpace):
    if search_space.database_schema is None:
        raise ValueError("search_space must contain a database_schema")
    return search_space.database_schema


def _hypothesis_prompt_context(hypothesis: Hypothesis | None = None) -> str:
    if hypothesis is None:
        return ""
    return f"*** HYPOTHESIS ***\n{hypothesis.content}"

class SemanticLinker:
    def __init__(
        self,
        model_name: str,
        model_provider: str = None,
        rules: SemanticRules | None = None,
    ):
        self.model_name = model_name
        self.model_provider = model_provider
        self.rules = rules or SemanticRules()

    def ground(self, state: WorkflowState) -> WorkflowState:
        semantic_linking_result = self.link(
            question=state.question,
            search_space=state.search_space,
            hypothesis=state.hypothesis,
        )
        database_schema = _database_schema_from_search_space(state.search_space)
        table_functions = {
            table_name.lower(): function
            for table_name, function in semantic_linking_result.table_functions.items()
        }
        enriched_table_schemas = [
            table_schema.model_copy(
                update={
                    "semantic_annotation": TableSemanticAnnotation(
                        function=table_functions[table_schema.name.lower()]
                    )
                },
            )
            if table_schema.name.lower() in table_functions
            else table_schema.model_copy()
            for table_schema in database_schema.table_schemas
        ]
        enriched_database_schema = database_schema.model_copy(
            update={
                "semantic_annotation": DatabaseSemanticAnnotation(
                    database_structure=semantic_linking_result.database_structure,
                    query_specific_content_analysis=(
                        semantic_linking_result.query_specific_content_analysis
                    ),
                ),
                "table_schemas": enriched_table_schemas,
            }
        )
        enriched_search_space = state.search_space.model_copy(
            update={
                "database_schema": enriched_database_schema,
                "semantic_linking_result": semantic_linking_result,
            }
        )
        return state.model_copy(update={"search_space": enriched_search_space})
    
    def link(
        self,
        question: Question,
        search_space: SearchSpace,
        hypothesis: Hypothesis | None = None,
    ) -> SemanticLinkingResult:
        natural_language_question = question.natural_language_question
        database_schema = _database_schema_from_search_space(search_space)
        hypothesis_context = _hypothesis_prompt_context(hypothesis)
    
        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(
            SemanticLinkingResult,
            method="function_calling",
        )
        critical_rules = self.rules.to_string()

        SEMANTIC_LINKING_PROMPT = f"""
            *** TASK CONTEXT ***
            You are a Senior Data Architect. You have full visibility of
            the database schema and a user question.
            Your goal is to perform **Semantic Linking**: Analyze the
            database structure and how it grounds the user’s intent.
            {critical_rules}
            *** USER QUESTION ***
            {natural_language_question}
            {hypothesis_context}
            *** DATABASE SCHEMA ***
            {database_schema.export_as_string()}
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
