import pytest

from piglets import LogicalPlan, LogicalPlanner


@pytest.fixture
def logical_planner(model_name) -> LogicalPlanner:
    return LogicalPlanner(model_name)


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

    assert isinstance(logical_plan, LogicalPlan)
    assert logical_plan.natural_language_query == natural_language_query
    assert isinstance(logical_plan.logical_steps, list)
    assert all(
        isinstance(step, str)
        for step in logical_plan.logical_steps
    )
