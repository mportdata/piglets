import pytest

from piglets import LogicalPlanner


@pytest.fixture
def logical_planner(model_name) -> LogicalPlanner:
    return LogicalPlanner(model_name)


def test_logical_planner(natural_language_query, logical_planner):
    logical_plan = logical_planner.plan(natural_language_query=natural_language_query)

    assert isinstance(logical_plan, dict)
    assert "logical_steps" in logical_plan
    assert isinstance(logical_plan["logical_steps"], list)
    assert all(isinstance(step, str) for step in logical_plan["logical_steps"])


def test_parallel_logical_planner(natural_language_query, logical_planner):
    num_plans = 3
    logical_plans = logical_planner.parallel_plan(
        natural_language_query=natural_language_query,
        num_plans=num_plans,
    )

    assert isinstance(logical_plans, list)
    assert len(logical_plans) == num_plans
    assert all(isinstance(logical_plan, dict) for logical_plan in logical_plans)
    assert all("logical_steps" in logical_plan for logical_plan in logical_plans)
    assert all(
        isinstance(logical_plan["logical_steps"], list)
        for logical_plan in logical_plans
    )
    assert all(
        isinstance(step, str)
        for logical_plan in logical_plans
        for step in logical_plan["logical_steps"]
    )
