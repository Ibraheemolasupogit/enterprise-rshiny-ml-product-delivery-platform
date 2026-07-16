# ADR 0031 - No Identifiers Or Outcome Fields In Shiny Input

Status: Accepted

Context: The API contract rejects leakage and identifier fields.

Decision: Shiny exposes admission-time synthetic predictors only.

Consequences: The UI cannot collect patient identifiers, admission identifiers, discharge fields, length of stay or target/outcome fields.

Alternatives considered: hidden advanced fields. Rejected because they create leakage and privacy risk.
