from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from langchain.chat_models import init_chat_model

from piglets.types import LogicalPlan
from piglets.utils import read_markdown_file


class LogicalPlanner():
    def __init__(self, model_name: str):
        file_path = Path(__file__).with_suffix(".md").resolve()
        self.system_instruction = read_markdown_file(file_path=file_path)

        llm = init_chat_model(model_name)
        llm = llm.with_structured_output(LogicalPlan)
        self.llm = llm

    def plan(self, natural_language_query: str) -> LogicalPlan:
        return self.llm.invoke(f"{self.system_instruction} \nUser question: {natural_language_query}")

    def parallel_plan(self, natural_language_query: str, num_plans: int = 5) -> list[LogicalPlan]:
        if num_plans < 1:
            raise ValueError("num_plans must be at least 1")

        with ThreadPoolExecutor(max_workers=num_plans) as executor:
            futures = [
                executor.submit(self.plan, natural_language_query)
                for _ in range(num_plans)
            ]
            return [future.result() for future in futures]
