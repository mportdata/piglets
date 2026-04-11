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