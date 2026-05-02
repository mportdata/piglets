# standard
- Identify columns that can anchor the requested time period or date filtering.
- Prefer explicit event dates, effective dates, or snapshot dates over ambiguous time-like fields.
- Note when the user question implies a time comparison or period-over-period analysis.

# strict
- Warn when the schema exposes multiple possible time anchors for the same business concept.
- Do not assume calendar logic, fiscal logic, or timezone handling unless the schema supports it.
- Warn when the requested time window cannot be grounded confidently in the schema.

# aggressive
- If no explicit time anchor exists, propose likely time columns from names, data types, and table purpose.
- Mark inferred temporal interpretations as assumptions.
- Rank candidate time columns by confidence.
