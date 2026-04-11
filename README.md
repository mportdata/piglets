# 🐷 piglets

A modular, pre-1.0 library of text-to-SQL planning tools.

## Status

`piglets` is currently an **alpha-stage** package. The API is expected to evolve before `1.0`.

## Current scope

### Planning

The first included primitive is a `LogicalPlanner` that turns a natural-language analytics question into an ordered list of abstract logical steps.

This keeps planning at the business-logic level before later schema grounding or SQL generation.

### Pruning

Pruning components are planned but not included yet.
