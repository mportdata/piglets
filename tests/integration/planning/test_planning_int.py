import pytest

from piglets import AggregatePlan, LogicalPlan


def test_logical_planner(question, logical_planner):
    logical_plan = logical_planner.plan(question=question)

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == question.natural_language_question
    assert isinstance(logical_plan.logical_steps, list)
    assert all(isinstance(step, str) for step in logical_plan.logical_steps)


def test_multi_sample_logical_planner(
    question,
    aggregate_logical_plan,
):
    logical_plan = aggregate_logical_plan

    assert isinstance(logical_plan, AggregatePlan)
    assert logical_plan.natural_language_query == question.natural_language_question
    assert isinstance(logical_plan.logical_steps, list)
    assert all(
        isinstance(step, str)
        for step in logical_plan.logical_steps
    )
    assert isinstance(logical_plan.sample_plans, list)
    assert len(logical_plan.sample_plans) > 1
    assert all(
        isinstance(plan, LogicalPlan)
        for plan in logical_plan.sample_plans
    )

def test_logical_plan_export_as_string(question, logical_planner):
    logical_plan = logical_planner.plan(question=question)
    plan_string = logical_plan.export_as_string()

    assert isinstance(plan_string, str)
    assert question.natural_language_question in plan_string
    for step in logical_plan.logical_steps:
        assert step in plan_string
