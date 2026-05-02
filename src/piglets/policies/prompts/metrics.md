# standard
- Prefer metrics that can be grounded in explicit numeric columns or clearly defined aggregations.
- Distinguish raw columns from derived calculations needed to answer the question.
- Identify likely numerator, denominator, grouping, and filtering fields when relevant.

# strict
- Do not assume business KPI definitions unless they are explicit in the schema or question.
- Warn when multiple metric definitions are plausible.
- Warn when answering the question would require derived logic not clearly supported by the schema.

# aggressive
- If the metric is not explicit, propose likely derivations from available numeric columns and keys.
- Mark inferred metric definitions as assumptions.
- Rank alternative metric interpretations by confidence.
