from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field


class LogicalSteps(BaseModel):
    """Structured LLM output containing only ordered logical steps."""

    logical_steps: list[str] = Field(
        description="Ordered logical planning steps for answering the query."
    )


class LogicalPlan(BaseModel):
    """A logical plan for how to answer a user's natural language query."""

    natural_language_query: str
    logical_steps: list[str]


class LogicalPlans(BaseModel):
    """A collection of logical plans for one natural language query."""

    natural_language_query: str
    logical_plans: list[LogicalPlan]

    def aggregate(self, model_name: str) -> LogicalPlan:
        """Aggregate multiple logical plan candidates into a single logical plan."""
        llm = init_chat_model(model_name)
        llm = llm.with_structured_output(LogicalSteps)
        plans_text = "\n\n".join(
            f"Plan {i + 1}:\n" + "\n".join(plan.logical_steps)
            for i, plan in enumerate(self.logical_plans)
        )

        plan_aggregator_prompt = f"""
            *** TASK CONTEXT ***
            We have collected {len(self.logical_plans)} draft logical plans.
            Synthesize them into a single, comprehensive Master
            Logical Plan. Ensure the steps cover all conditions, filters,
            joins, and aggregations required.
            *** USER QUESTION ***
            {self.natural_language_query}
            *** DRAFT PLANS ***
            {plans_text}
            *** OUTPUT ***
            Return exactly this JSON structure:
            {{
                "logical_steps": [
                    "1. Identify [Entity]...",
                    "2. Filter where [Condition]...",
                    "3. Link [Entity A] to [Entity B]...",
                    "4. Calculate [Aggregation]..."
                ]
            }}
        """

        aggregate_steps = llm.invoke(plan_aggregator_prompt)

        return LogicalPlan(
            natural_language_query=self.natural_language_query,
            logical_steps=aggregate_steps.logical_steps,
        )
