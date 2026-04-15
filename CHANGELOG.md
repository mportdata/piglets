# Changelog

## 0.1.8 - 2026-04-15

### Added
- Add `Pruner` with positive preservation, negative deletion, and dual-pathway schema pruning flows.
- Add pruning selection types: `PruningColumns`, `PreservationColumns`, `PreservationSet`, `DeletionColumns`, and `DeletionSet`.
- Add `Database.subtract()`, `Database.union()`, and `Database.export_as_string()` helpers for composing pruned schemas.
- Add `LogicalPlan.export_as_string()` for including compact plan context in pruning prompts.
- Add integration coverage for preservation, deletion, and dual-pathway pruning.
- Add unit coverage for database schema subtraction and union behavior.

### Changed
- Export pruning APIs from the root `piglets` package.
- Document dual-pathway pruning in the README.
- Add `sqlalchemy-bigquery` to the test dependency group used by BigQuery integration tests.

## 0.1.7 - 2026-04-14

### Added
- Add `DatabaseConnector` for inspecting BigQuery database schemas.
- Add typed database schema models: `Database`, `Table`, and `Column`.
- Add the `bigquery` optional dependency extra for installing BigQuery SQLAlchemy support.

### Changed
- Export `DatabaseConnector` from the root `piglets` package.
- Document BigQuery connector installation, configuration, and schema inspection in the README.
- Add `.env` to `.gitignore` for local database credentials and configuration.

## 0.1.6 - 2026-04-13

### Added
- Add `AggregatePlan.sample_plans` so aggregated logical plans retain their source candidate plans.
- Add optional dependency extras for additional LangChain model providers.

### Changed
- Thread `model_provider` through planner and aggregate model initialization.
- Document provider extras and the `sample_plans` aggregate-plan attribute in the README.

## 0.1.5 - 2026-04-12

### Changed
- Update `LogicalPlanner.plan()` to support multi-sample planning with `num_samples`.
- Replace `parallel_plan()` documentation and tests with the unified `plan(..., num_samples=...)` API.

### Fixed
- Ensure multi-sample planning generates individual candidate plans before aggregating them.

## 0.1.4 - 2026-04-12

### Added
- Add `LogicalPlans.aggregate()` for combining multiple logical plan candidates into one plan.

### Changed
- Use Pydantic models for logical planner structured outputs.
- Return `LogicalPlan` and `LogicalPlans` model objects from planner APIs.
- Combine the public planner API around `LogicalPlanner.plan(..., num_samples=...)`.

### Fixed
- Replace unsupported `list[str]` structured-output schemas with a `LogicalSteps` schema.

## 0.1.3 - 2026-04-11

### Added
- Add README installation and `LogicalPlanner.parallel_plan` usage examples.

### Fixed
- Correct README instructions for installing the `openai` optional dependency group.

## 0.1.2 - 2026-04-11

### Added
- Add `LogicalPlanner.parallel_plan` for generating multiple logical plans concurrently.
- Document the logical planner's relationship to the Apex-SQL paper.

### Changed
- Move logical planner integration coverage under `tests/integration`.
- Strengthen parallel logical planner test assertions.

## 0.1.1 - 2026-04-11

### Fixed
- Include `logical_planner.md` in packaged distributions so `LogicalPlanner` can load its prompt after installation from PyPI.

### Changed
- Run only unit tests in the publish workflow before building and publishing the package.

## 0.1.0 - 2026-04-11

Initial public alpha release of `piglets`.

### Included in this release
- Initial package structure for the `piglets` text-to-SQL toolkit.
- First planning primitive: `LogicalPlanner`.
- `LogicalPlan` typed output for structured logical planning steps.
- Prompt-driven logical planning flow for turning natural-language analytics questions into abstract plan steps.
- Integration test coverage for the logical planning flow.
- Packaging metadata for distribution on PyPI with `uv.lock` checked in for reproducible development.

### Notes
- This is a pre-1.0 release and the API is expected to change.
- Current focus is logical planning for analytics/text-to-SQL workflows.
