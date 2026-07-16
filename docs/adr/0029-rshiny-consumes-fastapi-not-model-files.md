# ADR 0029 - R-Shiny Consumes FastAPI, Not Model Files

Status: Accepted

Context: Shiny needs to demonstrate prediction without bypassing Milestone 7 governance controls.

Decision: Shiny calls the FastAPI scoring contract and never loads model artefacts, Python modules or DuckDB scoring data directly.

Consequences: Governance, authentication and schema validation remain centralized in FastAPI. Local development requires two processes.

Alternatives considered: direct R model loading, `reticulate`, and direct database scoring. These were rejected because they bypass governance.
