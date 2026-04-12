from pathlib import Path

import pytest

from piglets import LogicalPlan, LogicalPlanner, LogicalPlans
from piglets.planning.logical_planning import logical_planner
from piglets.types import plans


def test_logical_planner_prompt_is_available():
    prompt_path = Path(logical_planner.__file__).with_suffix(".md")

    assert prompt_path.is_file()


def test_parallel_plan_requires_at_least_one_plan():
    planner = LogicalPlanner.__new__(LogicalPlanner)

    with pytest.raises(ValueError, match="num_plans must be at least 1"):
        planner.parallel_plan("count chickens", num_plans=0)


def test_plan_wraps_structured_logical_steps(fake_logical_plan_llm):
    planner = LogicalPlanner.__new__(LogicalPlanner)
    planner.system_instruction = "Plan logically."
    planner.llm = fake_logical_plan_llm

    logical_plan = planner.plan("count piglets")

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == "count piglets"
    assert logical_plan.logical_steps == ["1. Count piglets."]


def test_logical_plans_aggregate_returns_logical_plan(
    monkeypatch,
    fake_logical_plan_llm,
):
    monkeypatch.setattr(
        plans,
        "init_chat_model",
        lambda model_name: fake_logical_plan_llm,
    )

    logical_plans = LogicalPlans(
        natural_language_query="count piglets",
        logical_plans=[
            LogicalPlan(
                natural_language_query="count piglets",
                logical_steps=["1. Identify piglet records."],
            )
        ],
    )

    logical_plan = logical_plans.aggregate("fake-model")

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == "count piglets"
    assert logical_plan.logical_steps == ["1. Count piglets."]
    assert "Plan 1" in fake_logical_plan_llm.prompts[0]
