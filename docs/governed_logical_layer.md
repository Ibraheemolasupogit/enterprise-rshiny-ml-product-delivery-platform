# Governed Logical Layer

Consumers should use curated views rather than raw tables. Curated views expose stable columns, quality statuses, eligibility flags, lineage, and governed exclusions.

The active provider is `denodo_compatible_local` and the active adapter is DuckDB. This is not real Denodo. The local layer establishes the contracts a future Denodo implementation must follow.

## Controls

Duplicate source keys and orphan records are recorded in quality tables and excluded from trusted curated views. Missing optional values are preserved with quality status. Inconsistent long-stay source flags retain both source and governed values. Operational exceptions such as occupied beds above staffed beds are labelled rather than hidden.

## Access

The logical-view client only allows allow-listed curated views. It validates view names and columns, parameterises filter values, enforces row limits, and does not provide arbitrary SQL access.
