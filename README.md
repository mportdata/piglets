# 🐷 piglets

A modular, pre-1.0 library of text-to-SQL planning tools.

## Status

`piglets` is currently an **alpha-stage** package. The API is expected to evolve before `1.0`.

## Current scope

### Planning

The first included primitive is a `LogicalPlanner` that turns a natural-language analytics question into an ordered list of abstract logical steps. The logical planner is an implementation of the planner found in the Apex-SQL paper [here](https://arxiv.org/pdf/2602.16720).

The `LogicalPlanner` has a `plan` method and a `parallel_plan` method.

Plan aggregation tools are coming soon.

### Pruning

Pruning components are planned but not included yet.
