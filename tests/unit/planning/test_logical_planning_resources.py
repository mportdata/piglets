from pathlib import Path

from piglets.planning.logical_planning import logical_planner


def test_logical_planner_prompt_is_available():
    prompt_path = Path(logical_planner.__file__).with_suffix(".md")

    assert prompt_path.is_file()
