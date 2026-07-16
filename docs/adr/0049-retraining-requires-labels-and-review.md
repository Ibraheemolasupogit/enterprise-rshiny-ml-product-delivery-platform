# ADR 0049: Retraining Requires Labels And Review

## Status

Accepted.

## Context

Monitoring can detect drift before labelled outcomes exist. Retraining without labels would fabricate supervision or misuse prediction events.

## Decision

Milestone 12 retraining eligibility requires governed monitoring review evidence, explicit labels, minimum labelled rows and both target classes. Drift alone is not sufficient.

## Consequences

The workflow can return `insufficient_evidence` or `defer_retraining`. This prevents unlabelled windows from becoming training data.
