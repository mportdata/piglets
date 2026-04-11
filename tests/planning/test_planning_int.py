from piglets import LogicalPlan, LogicalPlanner

def test_logical_planner(model_name, natural_language_query):
    logical_planner = LogicalPlanner(model_name)
    logical_plan = logical_planner.plan(natural_language_query=natural_language_query)
    print(logical_plan)
    assert isinstance(logical_plan, dict)
    assert "logical_steps" in logical_plan
    assert isinstance(logical_plan["logical_steps"], list)
    assert all(isinstance(step, str) for step in logical_plan["logical_steps"])