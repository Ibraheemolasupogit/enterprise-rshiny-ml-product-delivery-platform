# ADR 0009: Quality Fixtures Are Reconciled Not Silently Fixed

## Status

Accepted for Milestone 3.

## Context

Milestone 2 intentionally includes documented defects.

## Decision

Preserve source values, record treatment, quarantine or exclude where governed, and expose governed recalculations separately.

## Consequences

Evidence remains auditable. Curated views avoid hidden data repair.

## Alternatives Considered

Silent cleansing was rejected because it destroys fixture intent.
