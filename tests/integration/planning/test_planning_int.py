import pytest

from piglets import LogicalPlan, LogicalPlanner, LogicalPlans


@pytest.fixture
def logical_planner(model_name) -> LogicalPlanner:
    return LogicalPlanner(model_name)


def test_logical_planner(natural_language_query, logical_planner):
    logical_plan = logical_planner.plan(natural_language_query=natural_language_query)

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == natural_language_query
    assert isinstance(logical_plan.logical_steps, list)
    assert all(isinstance(step, str) for step in logical_plan.logical_steps)


def test_parallel_logical_planner(natural_language_query, logical_planner):
    num_plans = 3
    logical_plans = logical_planner.parallel_plan(
        natural_language_query=natural_language_query,
        num_plans=num_plans,
    )

    assert isinstance(logical_plans, LogicalPlans)
    assert logical_plans.natural_language_query == natural_language_query
    assert len(logical_plans.logical_plans) == num_plans
    assert all(
        isinstance(logical_plan, LogicalPlan)
        for logical_plan in logical_plans.logical_plans
    )
    assert all(
        logical_plan.natural_language_query == natural_language_query
        for logical_plan in logical_plans.logical_plans
    )
    assert all(
        isinstance(logical_plan.logical_steps, list)
        for logical_plan in logical_plans.logical_plans
    )
    assert all(
        isinstance(step, str)
        for logical_plan in logical_plans.logical_plans
        for step in logical_plan.logical_steps
    )
