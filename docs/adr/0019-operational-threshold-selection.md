# ADR 0019: Operational Threshold Selection

Status: Accepted

## Context

Default 0.5 thresholds may not match operational false-negative and false-positive costs.

## Decision

Milestone 6 uses a validation-only threshold grid with a minimum recall rule, precision tie-break, weighted cost tie-break, and stable final tie-break.

## Consequences

The selected threshold is auditable and locked before test evaluation.

## Alternatives Considered

Choosing thresholds by accuracy or visual preference was rejected.
