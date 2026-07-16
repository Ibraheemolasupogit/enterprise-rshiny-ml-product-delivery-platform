# ADR 0021: Candidate Models Remain Unregistered

Status: Accepted

## Context

Milestone 6 is model development, not registry or serving.

## Decision

Candidate artefacts stay under ignored `models/candidate`; no approved model registry or serving interface is created.

## Consequences

Milestone 7 can review candidate evidence for registration and serving. Milestone 6 cannot be mistaken for production approval.

## Alternatives Considered

Writing approved artefacts early was rejected. Creating serving endpoints early was rejected.
