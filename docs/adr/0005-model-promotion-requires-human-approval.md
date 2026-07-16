# ADR 0005: Model Promotion Requires Human Approval

## Status

Accepted for Milestone 1.

## Context

The future product will support operational decisions. Even with synthetic data, the delivery model should demonstrate safe governance for model changes.

## Decision

Future model promotion and controlled retraining will require human approval. Automated retraining may produce candidates, but it must not automatically promote models into an approved state.

## Consequences

The model registry, monitoring, and retraining workflows must capture review evidence and approval status. Delivery may be slower, but accountability is stronger.

## Alternatives Considered

Automatic promotion based only on metrics was rejected because it bypasses governance. Manual-only experimentation without evidence was rejected because it is not reproducible.
