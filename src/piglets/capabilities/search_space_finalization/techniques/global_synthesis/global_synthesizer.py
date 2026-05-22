import logging

from langchain.chat_models import init_chat_model

from piglets.database import DatabaseConnector
from piglets.types import (
    DatabaseProfileResult,
    Question,
    QueryResults,
    SearchSpace,
    SemanticLinkingResult,
    SynthesisRound,
    SynthesisResult,
    SynthesisRunResult,
    WorkflowState,
)


logger = logging.getLogger(__name__)


def _database_schema_from_search_space(search_space: SearchSpace):
    if search_space.database_schema is None:
        raise ValueError("search_space must contain a database_schema")
    return search_space.database_schema


class GlobalSynthesizer:
    def __init__(
            self,
            database_connector: DatabaseConnector,
            model_name: str,
            model_provider: str | None = None,
            search_space: SearchSpace | None = None,
    ):
        self.database_connector: DatabaseConnector = database_connector
        self.model_name: str = model_name
        self.model_provider = model_provider
        self.search_space: SearchSpace | None = search_space

    @property
    def database_schema(self):
        if self.search_space is None:
            raise ValueError("search_space must be set before synthesis")
        return _database_schema_from_search_space(self.search_space)

    def finalize(self, state: WorkflowState) -> WorkflowState:
        """Finalize the current search space from profile and synthesis evidence."""
        semantic_linking_result = state.search_space.semantic_linking_result
        if semantic_linking_result is None:
            raise ValueError("search_space must contain a semantic_linking_result")

        database_profile_result = state.search_space.database_profile_result
        if database_profile_result is None:
            raise ValueError("search_space must contain a database_profile_result")

        self.search_space = state.search_space
        synthesis_run_result = self.synthesize_observations(
            question=state.question,
            semantic_linking_result=semantic_linking_result,
            database_profile_result=database_profile_result,
            return_history=True,
        )
        if isinstance(synthesis_run_result, SynthesisResult):
            synthesis_result = synthesis_run_result
        else:
            synthesis_result = synthesis_run_result.final_result

        update = {"synthesis_run_result": synthesis_run_result}
        if synthesis_result.status == "[CONFIRM]":
            update["database_schema"] = synthesis_result.to_database_schema(
                self.database_schema
            )

        finalized_search_space = state.search_space.model_copy(update=update)
        return state.model_copy(update={"search_space": finalized_search_space})

    def _build_synthesis_prompt(
        self,
        question: Question,
        semantic_linking_result: SemanticLinkingResult,
        database_profile_result: DatabaseProfileResult,
        max_refine_rounds: int,
        round_number: int,
        previous_rounds: list[SynthesisRound],
    ) -> str:
        natural_language_question = question.natural_language_question
        previous_rounds_context = self._previous_rounds_to_string(previous_rounds)
        return f"""
            *** TASK CONTEXT ***
            You are the Lead Data Architect. We are synthesizing initial
            exploration findings.
            Review the [MARKED RELEVANT] and [MARKED
            IRRELEVANT] tables. Fix blind spots.
            *** USER QUESTION ***
            {natural_language_question}
            *** SEMANTIC ANALYSIS ***
            {semantic_linking_result}
            *** SCHEMA STATUS ***
            {database_profile_result.to_string(database_schema=self.database_schema)}
            {previous_rounds_context}
            *** YOUR MISSION ***
            Determine the final list of columns required to write the
            SQL query
            You must ensure the selected columns form a connected
            graph (tables can be joined) and cover all functional
            requirements of the query.
            *** SELECTION CRITERIA (FUNCTIONALITY) ***
            Keep a column if it serves one of the following purposes:
            1. **Identification**: Unique identifiers (IDs, Codes) needed
            to count or distinguish entities (Primary keys).
            2. **Linking**: Columns needed to join two tables together
            (Foreign Keys).
            3. **Filtering**: Columns involved in conditions (e.g., status=’Active’, date > 2023).
            4. **Aggregation**: Numerical columns for calculations
            (Sum, Avg, Max, Min).
            5. **Grouping & Sorting**: Columns used for ’GROUP BY’
            or ’ORDER BY’.
            6. **Direct Result**: Columns explicitly requested in the
            output.
            **Note on Multi-Path**: If multiple columns might serve the
            same purpose, KEEP ALL OF THEM. Alternative columns
            might help to construct another solution paths.
            **Note on Type of Entity**: DO NOT guess the type of an
            unspecified entity even you have some prior knowledge,
            e.g., if the query contains location entity like ’Riverside’,
            then ALL columns related to location (e.g., County, District,
            etc.) should be kept. Another example is ’Fresno County Office of Education’ which is actually a full name of a district.
            *** REJECTION REQUIREMENTS ***
            If a column was marked as **[MARKED RELEVANT]**
            in the Schema Status but you decide to **REJECT** it,
            you MUST include it in the ‘rejected_candidates‘ list with
            a ‘reject_reason‘ explaining why it is unnecessary. You
            can NOT reject a column for the reason that it is only a
            potentially useful column.
            *** INTERACTIVE PROCESS ***
            You can perform up to {max_refine_rounds} rounds of
            verification.
            This is round {round_number} of {max_refine_rounds}.
            - To EXPLORE: Output ‘exploration_queries‘ in JSON to
            test joins or content.
            - To FINISH: Output ‘[CONFIRM]‘ in the JSON (or just
            output the final refined_schema without queries).
            *** OUTPUT FORMAT ***
            You MUST explicitly list rejected candidates to prove you
            considered them.
            **IMPORTANT**: In ’rejected_candidates’, ONLY list
            columns that were previously marked RELEVANT but you
            decided to reject, OR columns that look ambiguous. Do
            NOT list obviously irrelevant columns to save space.
            ```json
            {{
                "refined_schema": {{
                    "table_name": {{
                        "relevant_columns": [
                            {{
                                "column_name": "...",
                                "relevance_reason": "Functional reason (e.g., Needed for Filtering)"
                            }}
                        ]
                    }}
                }},
                "rejected_candidates": [
                    {{
                        "table": "t1",
                        "column": "c1",
                        "reject_reason": "Originally marked relevant, but rejected because..."
                    }}
                ],
                "exploration_queries": ["SELECT 1 FROM t1 JOIN t2 ON t1.id=t2.id LIMIT 1"],
                "status": "EXPLORING" or "[CONFIRM]"
            }}
            ```
            Begin refinement:
        """

    @staticmethod
    def _previous_rounds_to_string(previous_rounds: list[SynthesisRound]) -> str:
        if not previous_rounds:
            return ""

        lines = [
            "*** PREVIOUS SYNTHESIS ATTEMPTS ***",
        ]
        for synthesis_round in previous_rounds:
            lines.extend([
                f"Round {synthesis_round.round_number}",
                f"Status: {synthesis_round.synthesis_result.status}",
                "Synthesis Response:",
                synthesis_round.synthesis_result.model_dump_json(indent=2),
            ])
            if synthesis_round.exploration_results is not None:
                lines.extend([
                    "Exploration Results:",
                    synthesis_round.exploration_results.to_string(
                        max_rows=10,
                        max_cell_length=80,
                    ),
                ])
            lines.append("")

        return "\n".join(lines)

    def _execute_exploration_queries(
        self,
        exploration_queries: list[str],
    ) -> QueryResults:
        query_results = [
            self.database_connector.execute_query(exploration_query)
            for exploration_query in exploration_queries
        ]
        return QueryResults(query_results=query_results)

    def synthesize_observations(
            self,
            question: Question,
            semantic_linking_result: SemanticLinkingResult,
            database_profile_result: DatabaseProfileResult,
            max_refine_rounds: int = 10,
            return_history: bool = True,
    ) -> SynthesisResult | SynthesisRunResult:
        if max_refine_rounds < 1:
            raise ValueError("max_refine_rounds must be greater than or equal to 1")

        llm = init_chat_model(model=self.model_name, model_provider=self.model_provider)
        llm = llm.with_structured_output(SynthesisResult, method="function_calling")
        synthesis_rounds: list[SynthesisRound] = []
        final_result: SynthesisResult | None = None
        reached_limit = False

        for round_number in range(1, max_refine_rounds + 1):
            prompt = self._build_synthesis_prompt(
                question=question,
                semantic_linking_result=semantic_linking_result,
                database_profile_result=database_profile_result,
                max_refine_rounds=max_refine_rounds,
                round_number=round_number,
                previous_rounds=synthesis_rounds,
            )
            synthesis_result: SynthesisResult = llm.invoke(prompt)
            exploration_results = None
            final_result = synthesis_result

            if synthesis_result.status == "[CONFIRM]":
                synthesis_rounds.append(
                    SynthesisRound(
                        round_number=round_number,
                        synthesis_result=synthesis_result,
                    )
                )
                break

            if not synthesis_result.exploration_queries:
                logger.warning(
                    "Synthesis requested exploration in round %s without queries",
                    round_number,
                )
                synthesis_rounds.append(
                    SynthesisRound(
                        round_number=round_number,
                        synthesis_result=synthesis_result,
                    )
                )
                break

            if round_number == max_refine_rounds:
                reached_limit = True
                synthesis_rounds.append(
                    SynthesisRound(
                        round_number=round_number,
                        synthesis_result=synthesis_result,
                    )
                )
                break

            exploration_results = self._execute_exploration_queries(
                synthesis_result.exploration_queries
            )
            synthesis_rounds.append(
                SynthesisRound(
                    round_number=round_number,
                    synthesis_result=synthesis_result,
                    exploration_results=exploration_results,
                )
            )

        if final_result is None:
            raise RuntimeError("Synthesis did not produce a result")

        if not return_history:
            return final_result

        return SynthesisRunResult(
            final_result=final_result,
            rounds=synthesis_rounds,
            reached_limit=reached_limit,
        )
