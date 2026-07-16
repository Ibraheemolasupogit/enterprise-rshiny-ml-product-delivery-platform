# ADR 0042: Monitoring Is Review Only

## Status

Accepted.

## Context

Milestone 11 needs data quality, drift, prediction, performance, calibration and operational monitoring evidence. It must not silently convert alerts into model lifecycle actions.

## Decision

Monitoring alerts create human review obligations only. The monitoring review record keeps automatic action as none, retraining as not implemented, registry mutation as none and model replacement as none.

## Consequences

The product can detect concerning movement without bypassing governance. Future retraining or promotion work must be implemented as a separate controlled workflow with explicit approval evidence.
