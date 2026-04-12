from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langchain.chat_models import init_chat_model

from piglets.types import LogicalPlan, LogicalPlans, LogicalSteps
from piglets.utils import read_markdown_file


class LogicalPlanner():
    def __init__(self, model_name: str):
        file_path = Path(__file__).with_suffix(".md").resolve()
        self.system_instruction = read_markdown_file(file_path=file_path)
        self.model_name = model_name
        llm = init_chat_model(model_name)
        self.llm = llm.with_structured_output(LogicalSteps)

    def _plan_once(self, natural_language_query: str) -> LogicalPlan:
        logical_steps = self.llm.invoke(
            f"{self.system_instruction} \nUser question: {natural_language_query}"
        )

        return LogicalPlan(
            natural_language_query=natural_language_query,
            logical_steps=logical_steps.logical_steps,
        )

    def _plan_many(self, natural_language_query: str, num_samples: int = 5) -> LogicalPlans:
        if num_samples < 1:
            raise ValueError("num_samples must be at least 1.")

        with ThreadPoolExecutor(max_workers=num_samples) as executor:
            futures = [
                executor.submit(self._plan_once, natural_language_query)
                for _ in range(num_samples)
            ]
            logical_plans = LogicalPlans(
                natural_language_query=natural_language_query,
                logical_plans=[future.result() for future in futures],
            )
        return logical_plans

    def plan(self, natural_language_query: str, num_samples: int = 1) -> LogicalPlan:
        if num_samples < 1:
            raise ValueError("num_samples must be at least 1.")
        elif num_samples == 1:
            return self._plan_once(
                natural_language_query=natural_language_query
            )
        elif num_samples > 1:
            logical_plans = self._plan_many(
                natural_language_query=natural_language_query,
                num_samples=num_samples,
            )
            return logical_plans.aggregate(model_name=self.model_name)
