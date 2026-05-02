# standard
- Prefer explicit primary-key and foreign-key relationships.
- Identify the shortest valid join path between required tables.
- Avoid joins that are not needed to answer the user question.

# strict
- Only accept joins supported by explicit schema relationships or strong evidence.
- Warn when multiple join paths are possible.
- Warn when a join may create fanout or duplicate rows.
- Do not infer joins from similar names alone.

# aggressive
- If explicit relationships are missing, propose likely joins using naming conventions and compatible data types.
- Mark inferred joins as assumptions.
- Rank inferred joins by confidence.
