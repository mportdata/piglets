from concurrent.futures import ThreadPoolExecutor
from langchain.chat_models import init_chat_model
from pathlib import Path

from piglets.types import (
    AggregatePlan,
    Hypothesis,
    LogicalPlan,
    LogicalPlans,
    LogicalSteps,
    Question,
)
from piglets.utils import read_markdown_file


class LogicalPlanner():
    def __init__(
        self,
        model_name: str,
        model_provider: str = None,
        num_samples: int = 1,
    ):
        if num_samples < 1:
            raise ValueError("num_samples must be at least 1.")

        file_path = Path(__file__).with_suffix(".md").resolve()
        self.system_instruction = read_markdown_file(file_path=file_path)
        self.model_name = model_name
        self.num_samples = num_samples
        llm = init_chat_model(model=model_name, model_provider=model_provider)
        self.model_provider = model_provider
        self.llm = llm.with_structured_output(LogicalSteps)

    def _plan_once(self, question: Question) -> LogicalPlan:
        natural_language_question = question.natural_language_question
        logical_steps = self.llm.invoke(
            f"{self.system_instruction} \nUser question: {natural_language_question}"
        )

        return LogicalPlan(
            natural_language_query=natural_language_question,
            logical_steps=logical_steps.logical_steps,
        )

    def _plan_many(self, question: Question) -> LogicalPlans:
        with ThreadPoolExecutor(max_workers=self.num_samples) as executor:
            futures = [
                executor.submit(self._plan_once, question)
                for _ in range(self.num_samples)
            ]
            logical_plans = LogicalPlans(
                natural_language_query=question.natural_language_question,
                logical_plans=[future.result() for future in futures],
            )
        return logical_plans

    def plan(self, question: Question) -> LogicalPlan | AggregatePlan:
        if self.num_samples == 1:
            return self._plan_once(
                question=question
            )
        elif self.num_samples > 1:
            logical_plans = self._plan_many(
                question=question,
            )
            return logical_plans.aggregate(
                model_name=self.model_name,
                model_provider=self.model_provider,
            )

    def generate(self, question: Question) -> Hypothesis:
        logical_plan = self.plan(question=question)
        return Hypothesis(
            question=question,
            content=logical_plan.export_as_string(),
            technique="logical_planning",
            technique_parameters={
                "num_samples": self.num_samples,
            },
        )
