# ADR 0016: Validation-Led Model Selection

Status: Accepted

## Context

Milestone 6 needs a deterministic recommendation without using the test set for tuning.

## Decision

Candidate comparison and recommendation use validation metrics only. The test set is reserved for final locked evaluation.

## Consequences

Selection is reproducible and auditable. Small validation size limits confidence, so the recommendation remains a review candidate rather than approval.

## Alternatives Considered

Using test metrics for selection was rejected. Manual visual selection was rejected because it is not reproducible.
