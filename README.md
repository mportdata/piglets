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

Use `DatabaseConnector` to inspect a database and return a typed schema. Pass either a SQLAlchemy `URL`, a connection string, or one of Piglets' helper URL classes.

```python
from piglets import BigQueryURL, DatabaseConnector

database_connector = DatabaseConnector(
    connection=BigQueryURL(
        dataset="my_bigquery_dataset",
    ),
)

database = database_connector.get_database_schema()

print(database.name)
for table in database.tables:
    print(table.name)
    for column in table.columns:
        print(f"- {column.name} ({column.data_type})")
```

BigQuery connections can include an explicit GCP project ID:

```python
database_connector = DatabaseConnector(
    connection=BigQueryURL(
        project_id="my-gcp-project",
        dataset="my_bigquery_dataset",
    ),
)
```

### Supported databases

`DatabaseConnector` supports any database URL accepted by SQLAlchemy. Use `URL` for SQLAlchemy-native dialects and Piglets helper URL classes where the connection string has backend-specific parameters.

| Backend | Connection object | Install requirement | Notes |
| --- | --- | --- | --- |
| SQLAlchemy-supported databases | `URL` or a connection string | Depends on the SQLAlchemy dialect and DBAPI driver | Use this for SQLite, PostgreSQL, MySQL, Oracle, SQL Server, and other standard SQLAlchemy dialects. |
| BigQuery | `BigQueryURL` | `piglets[bigquery]` | Uses `GOOGLE_CLOUD_PROJECT_ID` when `project_id` is omitted. |
| Snowflake | `SnowflakeURL` | `piglets[snowflake]` | Builds Snowflake URLs from explicit connection parameters. |
| DuckDB | `DuckDBURL` | `piglets[duckdb]` | Builds local or in-memory DuckDB URLs. |
| MotherDuck | `MotherDuckURL` | `piglets[duckdb]` | Builds MotherDuck URLs through the DuckDB SQLAlchemy dialect. |

For a SQLAlchemy-native database, create a standard SQLAlchemy `URL`:

```python
from piglets import DatabaseConnector, URL

database_connector = DatabaseConnector(
    connection=URL.create(
        drivername="sqlite",
        database="example.db",
    ),
)
database = database_connector.get_database_schema()
```

For a backend with a Piglets helper class, pass that URL object directly:

```python
from piglets import DatabaseConnector, SnowflakeURL

database_connector = DatabaseConnector(
    connection=SnowflakeURL(
        account="my-account",
        user="my-user",
        password="my-password",
        database="SNOWFLAKE_SAMPLE_DATA",
        schema="TPCH_SF1",
    ),
)
database = database_connector.get_database_schema()
```

### Dual-pathway pruning

Use `Pruner` to reduce a database schema with both preservation and deletion signals. The preservation pathway selects tables and columns that look useful for the query. The deletion pathway removes tables and columns that look irrelevant. `dual_pathway_pruning()` combines both paths into a final `Database` schema.

```python
from piglets import BigQueryURL, DatabaseConnector, LogicalPlanner, Pruner

question = "Which tags saw the largest increase in average answer score from 2022 to 2023, considering only questions with at least 5 answers?"

logical_planner = LogicalPlanner("gpt-5.2")
logical_plan = logical_planner.plan(
    natural_language_query=question,
    num_samples=3,
)

database_connector = DatabaseConnector(
    connection=BigQueryURL(
        dataset="stack_overflow",
    ),
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
