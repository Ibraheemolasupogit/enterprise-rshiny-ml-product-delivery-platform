# ADR 0045: R-Shiny Monitoring Is Read Only

## Status

Accepted.

## Context

Operational users need to inspect monitoring evidence in the R-Shiny product, but model lifecycle state is governed separately.

## Decision

The Monitoring page reads committed aggregate evidence and displays status, section metrics, alerts and next-step guidance. It provides no controls for retraining, promotion, approval, activation, deployment, rollback, threshold changes or calibration changes.

## Consequences

The user interface can support review without becoming a governance bypass. Tests and validators check that mutation controls are absent.
