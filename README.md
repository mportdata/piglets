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

Install the optional dependency for the model provider you use. For OpenAI:

**venv**
```bash
pip install "piglets[openai]"
```
**uv**
```bash
uv add "piglets[openai]"
```

Other provider extras include `anthropic`, `google_genai`, `google_vertexai`, `bedrock`, `cohere`, `mistralai`, `groq`, `ollama`, and `openrouter`.

Install the optional dependency for the database backend you use. For BigQuery:

**venv**
```bash
pip install "piglets[bigquery]"
```
**uv**
```bash
uv add "piglets[bigquery]"
```

### Logical planning

Use `gpt-5.2` to generate 3 logical plans from a natural language query.

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

# inspect the candidate plans used to create the aggregate
print(f"Aggregated from {len(logical_plan.sample_plans)} sample plans.")
```

```
>>> Step 1:
>>> 1. Identify all piglet birth (or piglet addition) events with their event dates and piglet counts.
>>> Step 2:
>>> 2. Filter the events to the Q4 2025 date range (Oct 1, 2025 through Dec 31, 2025).
>>> Step 3:
>>> 3. Assign each event to a calendar week within that quarter using a consistent week definition (e.g., week starting Monday or Sunday).
>>> Aggregated from 3 sample plans.
...
```

### Database connector

**Note:** currently only supports `bigquery`, support for all other popular database types coming soon. 

Use `DatabaseConnector` to inspect a supported database and return a typed schema.

```python
from piglets import DatabaseConnector

database_connector = DatabaseConnector(
    database_type="bigquery",
    database_name="my_bigquery_dataset",
)

database = database_connector.get_database_schema()

print(database.name)
for table in database.tables:
    print(table.name)
    for column in table.columns:
        print(f"- {column.name} ({column.data_type})")
```

BigQuery connections use the `GOOGLE_CLOUD_PROJECT_ID` environment variable by default. You can also pass `gcp_project_id` directly:

```python
database_connector = DatabaseConnector(
    database_type="bigquery",
    database_name="my_bigquery_dataset",
    gcp_project_id="my-gcp-project",
)
```

### Dual-pathway pruning

Use `Pruner` to reduce a database schema with both preservation and deletion signals. The preservation pathway selects tables and columns that look useful for the query. The deletion pathway removes tables and columns that look irrelevant. `dual_pathway_pruning()` combines both paths into a final `Database` schema.

```python
from piglets import DatabaseConnector, LogicalPlanner, Pruner

question = "Which tags saw the largest increase in average answer score from 2022 to 2023, considering only questions with at least 5 answers?"

logical_planner = LogicalPlanner("gpt-5.2")
logical_plan = logical_planner.plan(
    natural_language_query=question,
    num_samples=3,
)

database_connector = DatabaseConnector(
    database_type="bigquery",
    database_name="stack_overflow",
)
database = database_connector.get_database_schema()

pruner = Pruner(model_name="gpt-5.2")
pruned_database = pruner.dual_pathway_pruning(
    natural_language_query=question,
    database=database,
    logical_plan=logical_plan,
)

print(pruned_database.export_as_string())
```

## Current scope

### Database

`DatabaseConnector` currently supports BigQuery. It connects to a database by `database_name` and returns a `Database` object containing `Table` and `Column` objects.

### Planning

The first included primitive is a `LogicalPlanner` that turns a natural-language analytics question into an ordered list of abstract logical steps.

The `LogicalPlanner` has a `plan` method that can generate one plan or sample multiple plans and aggregate them with `num_samples`.

Plan aggregation is available through `LogicalPlans.aggregate()`.
Aggregated plans include a `sample_plans` attribute containing the candidate `LogicalPlan` objects used to produce the final plan.

### Pruning

`Pruner` supports preservation pruning, deletion pruning, and dual-pathway pruning. Preservation pruning returns a `PreservationSet` of useful tables and columns. Deletion pruning returns a `DeletionSet` of irrelevant tables and columns. Dual-pathway pruning combines both into a final pruned `Database`.
