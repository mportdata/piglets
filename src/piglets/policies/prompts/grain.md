# standard
- Identify the row grain of the main tables before assigning roles.
- Prefer tables whose grain matches the user question most directly.
- Call out when answer columns and filtering columns live at different grains.

# strict
- Warn when combining tables at incompatible grains may duplicate or suppress results.
- Do not assume rollups or deduplicated entities unless the schema shows them.
- Distinguish entity-level, event-level, and snapshot-level tables explicitly.

# aggressive
- If the grain is not explicit, infer the most likely grain from keys, timestamps, and column patterns.
- Mark inferred grain assumptions clearly.
- Rank possible grains when multiple are plausible.
