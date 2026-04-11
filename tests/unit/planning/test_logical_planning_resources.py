from pathlib import Path

import pytest

from piglets import LogicalPlanner
from piglets.planning.logical_planning import logical_planner


def test_logical_planner_prompt_is_available():
    prompt_path = Path(logical_planner.__file__).with_suffix(".md")

    assert prompt_path.is_file()


def test_parallel_plan_requires_at_least_one_plan():
    planner = LogicalPlanner.__new__(LogicalPlanner)

    with pytest.raises(ValueError, match="num_plans must be at least 1"):
        planner.parallel_plan("count chickens", num_plans=0)
