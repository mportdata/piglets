# 🐷 piglets

A modular, pre-1.0 library of text-to-SQL planning tools.

## Status

`piglets` is currently an **alpha-stage** package. The API is expected to evolve before `1.0`.

## Get started

### Install

**venv**
```bash
pip install piglets
```
**uv**
```bash
uv add piglets
```

### Example

Use `gpt-5.2` to generate 3 logical plans from a natural language query.

#### Install optional OpenAI dependencies

**venv**
```bash
pip install "piglets[openai]"
```
**uv**
```bash
uv add "piglets[openai]"
```

```python
from piglets import LogicalPlanner

# initialise a logical planner
logical_planner = LogicalPlanner('gpt-5.2')

# generate 3 logical plans
logical_plans = logical_planner.parallel_plan(
    natural_language_query="What was the average number of piglets per week for Q4 2025?",
    num_plans=3
)

# print each logical plan
for i in range(len(logical_plans)):
    print(f"Logical Plan {i + 1}: ")
    steps = logical_plans[i]["logical_steps"]
    for j in range(len(steps)):
        print(f"Step {j + 1}: ")
        print(steps[j])
```

```
>>> Logical Plan 1:
>>> Step 1:
>>> 1. Identify all piglet birth (or piglet addition) events with their event dates and piglet counts.
>>> Step 2:
>>> 2. Filter the events to the Q4 2025 date range (Oct 1, 2025 through Dec 31, 2025).
>>> Step 3:
>>> 3. Assign each event to a calendar week within that quarter using a consistent week definition (e.g., week starting Monday or Sunday).
...
```

## Current scope

### Planning

The first included primitive is a `LogicalPlanner` that turns a natural-language analytics question into an ordered list of abstract logical steps. The logical planner is an implementation of the planner found in the Apex-SQL paper [here](https://arxiv.org/pdf/2602.16720).

The `LogicalPlanner` has a `plan` method and a `parallel_plan` method.

Plan aggregation tools are coming soon.

### Pruning

Pruning components are planned but not included yet.
