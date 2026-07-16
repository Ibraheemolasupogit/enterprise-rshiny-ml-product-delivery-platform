# 0022 Local Filesystem Model Registry

Status: Accepted

Context: Milestone 7 needs reproducible registry behavior without external platforms.

Decision: Use a local filesystem registry with committed metadata and ignored binary artefacts.

Consequences: Registry behavior is testable locally, but it is not an enterprise registry service.

Alternatives considered: MLflow and SAS Viya were deferred because they are unnecessary or unavailable for this milestone.
