# ADR 0035: Cohort Scoring Uses FastAPI Batch Endpoint

Status: Accepted

Context: The R-Shiny product must not load Python model files or score locally.

Decision: Synthetic cohort scoring uses `/v1/predict/batch` through the existing authenticated FastAPI boundary.

Consequences: Batch validation happens in R, but scoring, thresholding, risk bands, and review labels remain service-owned.

Alternatives considered: Repeated single-record calls were rejected because the batch endpoint already provides a clearer ordering contract.
