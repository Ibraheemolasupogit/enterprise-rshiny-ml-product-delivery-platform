# ADR 0041: Export Contract Excludes Sensitive And Hidden Fields

Status: Accepted

Context: Synthetic cohort results are useful to export, but raw inputs and technical details are unnecessary.

Decision: Exports include only safe result fields, candidate identifier, synthetic-data statement, and export timestamp.

Consequences: CSV exports avoid API keys, paths, stack traces, hidden transformed features, raw inputs, identifiers, and outcomes.

Alternatives considered: Exporting full uploaded rows was rejected to keep the product bounded and privacy-aware.
