# Changelog

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
