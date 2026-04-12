# 🐷 piglets

A modular library of text-to-SQL tools.

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

# generate 3 logical plan samples and aggregate them
logical_plan = logical_planner.plan(
    natural_language_query="What was the average number of piglets per week for Q4 2025?",
    num_samples=3,
)

# print the aggregated logical plan
for i, step in enumerate(logical_plan.logical_steps):
    print(f"Step {i + 1}: ")
    print(step)
```

```
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

The `LogicalPlanner` has a `plan` method that can generate one plan or sample multiple plans and aggregate them with `num_samples`.

Plan aggregation is available through `LogicalPlans.aggregate()`.

### Pruning

Pruning components are planned but not included yet.
