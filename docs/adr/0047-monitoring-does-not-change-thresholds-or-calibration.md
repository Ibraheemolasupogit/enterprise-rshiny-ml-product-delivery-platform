# ADR 0047: Monitoring Does Not Change Thresholds Or Calibration

## Status

Accepted.

## Context

Threshold and calibration changes alter the prediction contract and user-facing risk interpretation.

## Decision

Milestone 11 monitoring may report threshold-related and calibration-related evidence, but it must not update thresholds, recalibrate probabilities or change registry metadata. Any such change requires a future controlled governance workflow.

## Consequences

Monitoring remains an observation layer. Existing threshold, calibration and registry evidence stay locked unless an explicit later milestone introduces approved mutation behavior.
