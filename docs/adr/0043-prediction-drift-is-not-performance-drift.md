# ADR 0043: Prediction Drift Is Not Performance Drift

## Status

Accepted.

## Context

Score distributions can move before current outcome labels are available. Treating that movement as performance degradation would overstate the evidence.

## Decision

Prediction drift reports distribution movement only and records that it is not a performance claim without labels. Performance monitoring is evaluated separately and returns insufficient evidence when labels are unavailable or too sparse.

## Consequences

Reviewers can see score movement early while avoiding unsupported claims about model quality. Labelled evidence remains required before performance degradation is asserted.
