from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from piglets.types import LogicalSteps


class FakeLLM:
    def __init__(self):
        self.prompts = []
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self


class FakeLogicalPlanLLM(FakeLLM):
    def invoke(self, prompt):
        self.prompts.append(prompt)
        schema = self.schema or LogicalSteps
        return schema(logical_steps=["1. Count piglets."])


@pytest.fixture
def fake_logical_plan_llm() -> FakeLogicalPlanLLM:
    return FakeLogicalPlanLLM()


@pytest.fixture
def model_name() -> str:
    return "gpt-5.2"

@pytest.fixture
def natural_language_query() -> str:
    return "Which tags saw the largest increase in average answer score from 2022 to 2023, considering only questions with at least 5 answers?"
