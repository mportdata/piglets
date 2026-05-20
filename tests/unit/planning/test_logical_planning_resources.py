from pathlib import Path

import pytest

from piglets import (
    AggregatePlan,
    Hypothesis,
    LogicalPlan,
    LogicalPlanner,
    LogicalPlans,
    Question,
)
from piglets.capabilities.hypothesis_generation import (
    HypothesisGenerator,
    LogicalPlanner as CapabilityLogicalPlanner,
)
from piglets.capabilities.hypothesis_generation.techniques.logical_planning import (
    logical_planner as capability_logical_planner,
)
from piglets.planning import LogicalPlanner as PlanningLogicalPlanner
from piglets.planning.logical_planning import (
    LogicalPlanner as LogicalPlanningLogicalPlanner,
)
from piglets.types import plans


def test_logical_planner_prompt_is_available():
    prompt_path = Path(capability_logical_planner.__file__).with_suffix(".md")

    assert prompt_path.is_file()


def test_logical_planner_compatibility_imports_resolve_to_same_class():
    assert LogicalPlanner is CapabilityLogicalPlanner
    assert LogicalPlanner is PlanningLogicalPlanner
    assert LogicalPlanner is LogicalPlanningLogicalPlanner


def test_hypothesis_generator_protocol_is_exported():
    assert HypothesisGenerator.__name__ == "HypothesisGenerator"
    assert isinstance(LogicalPlanner.__new__(LogicalPlanner), HypothesisGenerator)


def test_plan_requires_at_least_one_sample():
    with pytest.raises(ValueError, match="num_samples must be at least 1"):
        LogicalPlanner(model_name="fake-model", num_samples=0)


def test_plan_wraps_structured_logical_steps(fake_logical_plan_llm):
    planner = LogicalPlanner.__new__(LogicalPlanner)
    planner.system_instruction = "Plan logically."
    planner.num_samples = 1
    planner.llm = fake_logical_plan_llm

    question = Question(natural_language_question="count piglets")
    logical_plan = planner.plan(question)

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == "count piglets"
    assert logical_plan.logical_steps == ["1. Count piglets."]


def test_generate_wraps_logical_plan_as_hypothesis(fake_logical_plan_llm):
    planner = LogicalPlanner.__new__(LogicalPlanner)
    planner.system_instruction = "Plan logically."
    planner.num_samples = 1
    planner.llm = fake_logical_plan_llm

    question = Question(natural_language_question="count piglets")
    hypothesis = planner.generate(question)

    assert isinstance(hypothesis, Hypothesis)
    assert hypothesis.question is question
    assert hypothesis.content == (
        "Logical Plan for Query: count piglets\n1. Count piglets."
    )
    assert hypothesis.technique == "logical_planning"
    assert hypothesis.technique_parameters == {"num_samples": 1}


def test_plan_aggregates_multiple_samples(monkeypatch, fake_logical_plan_llm):
    monkeypatch.setattr(
        plans,
        "init_chat_model",
        lambda model, model_provider=None: fake_logical_plan_llm,
    )

    planner = LogicalPlanner.__new__(LogicalPlanner)
    planner.model_name = "fake-model"
    planner.model_provider = None
    planner.num_samples = 3
    planner.system_instruction = "Plan logically."
    planner.llm = fake_logical_plan_llm

    question = Question(natural_language_question="count piglets")
    logical_plan = planner.plan(question)

    assert isinstance(logical_plan, AggregatePlan)
    assert logical_plan.natural_language_query == "count piglets"
    assert logical_plan.logical_steps == ["1. Count piglets."]
    assert len(logical_plan.sample_plans) == 3
    assert all(isinstance(plan, LogicalPlan) for plan in logical_plan.sample_plans)
    assert all(
        plan.natural_language_query == "count piglets"
        for plan in logical_plan.sample_plans
    )
    assert all(
        plan.logical_steps == ["1. Count piglets."]
        for plan in logical_plan.sample_plans
    )
    assert len(fake_logical_plan_llm.prompts) == 4


def test_logical_plans_aggregate_returns_logical_plan(
    monkeypatch,
    fake_logical_plan_llm,
):
    monkeypatch.setattr(
        plans,
        "init_chat_model",
        lambda model, model_provider=None: fake_logical_plan_llm,
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

    assert isinstance(logical_plan, AggregatePlan)
    assert logical_plan.natural_language_query == "count piglets"
    assert logical_plan.logical_steps == ["1. Count piglets."]
    assert logical_plan.sample_plans == logical_plans.logical_plans
    assert "Plan 1" in fake_logical_plan_llm.prompts[0]
