# ADR 0011: Admission-Time Prediction Contract

Status: Accepted

## Context

The product needs a stable feature foundation before any model work begins. Predictors must be available at or shortly after admission so future estimates can support operational planning without relying on discharge outcomes.

## Decision

Milestone 5 defines one admission as the unit of analysis, `long_stay_flag_governed` as the target, and shortly-after-admission as the prediction point. Outcome, discharge, readmission, and target-derived fields are excluded from predictors.

## Consequences

Feature engineering can be validated without training a model. Future model development inherits a clear availability boundary and must not reinterpret future outcome fields as predictors.

## Alternatives Considered

Using discharge-time features was rejected because it would leak the answer. Deferring the contract to model development was rejected because feature design would be ambiguous.
