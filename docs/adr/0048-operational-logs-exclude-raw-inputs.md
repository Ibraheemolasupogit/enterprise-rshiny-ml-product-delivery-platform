# ADR 0048: Operational Logs Exclude Raw Inputs

## Status

Accepted.

## Context

Operational monitoring needs latency, success, error and model-version evidence, but raw request payloads could contain sensitive values.

## Decision

Serving event logs and monitoring fixtures record operational metadata, model output summaries, review-mode status and errors without raw inputs, patient identifiers, admission identifiers, API keys or secrets.

## Consequences

Operational monitoring remains useful for service review while respecting the repository security and synthetic-data-only boundaries.
