# ADR 0017: Test-Set Lock

Status: Accepted

## Context

The test set must estimate final locked behaviour rather than influence model choice.

## Decision

Milestone 6 records `test_set_used_for_selection: false` and evaluates test data only after model, calibration, and threshold selection.

## Consequences

Repeated builds reproduce the same locked result but do not alter selection from test metrics.

## Alternatives Considered

Iterating on test results was rejected because it would invalidate the holdout evidence.
