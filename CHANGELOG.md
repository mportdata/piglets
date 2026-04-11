# Changelog

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
