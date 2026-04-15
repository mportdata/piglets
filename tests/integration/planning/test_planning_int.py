import pytest

from piglets import AggregatePlan, LogicalPlan


def test_logical_planner(natural_language_query, logical_planner):
    logical_plan = logical_planner.plan(natural_language_query=natural_language_query)

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == natural_language_query
    assert isinstance(logical_plan.logical_steps, list)
    assert all(isinstance(step, str) for step in logical_plan.logical_steps)


def test_multi_sample_logical_planner(natural_language_query, logical_planner):
    num_samples = 3
    logical_plan = logical_planner.plan(
        natural_language_query=natural_language_query,
        num_samples=num_samples,
    )

    assert isinstance(logical_plan, AggregatePlan)
    assert logical_plan.natural_language_query == natural_language_query
    assert isinstance(logical_plan.logical_steps, list)
    assert all(
        isinstance(step, str)
        for step in logical_plan.logical_steps
    )
    assert isinstance(logical_plan.sample_plans, list)
    assert len(logical_plan.sample_plans) == num_samples
    assert all(
        isinstance(plan, LogicalPlan)
        for plan in logical_plan.sample_plans
    )

def test_logical_plan_export_as_string(natural_language_query, logical_planner):
    logical_plan = logical_planner.plan(natural_language_query=natural_language_query)
    plan_string = logical_plan.export_as_string()

    assert isinstance(plan_string, str)
    assert natural_language_query in plan_string
    for step in logical_plan.logical_steps:
        assert step in plan_string