# ADR 0018: Probability Calibration Before Serving

Status: Accepted

## Context

Operational decision support needs interpretable risk probabilities and thresholds.

## Decision

Milestone 6 evaluates calibration before any future serving milestone. Sigmoid calibration is permitted; isotonic requires a minimum validation sample size.

## Consequences

The current small validation set blocks isotonic calibration. Serving remains future work.

## Alternatives Considered

Skipping calibration was rejected. Fitting calibration on test data was rejected.
