# ADR 0008: Governed Views Over Raw Access

## Status

Accepted for Milestone 3.

## Context

Future data science and R-Shiny consumers need reusable source contracts.

## Decision

Expose curated governed views and keep raw access internal.

## Consequences

Consumers receive quality statuses, eligibility flags, and lineage. Raw defects remain traceable.

## Alternatives Considered

Direct raw access was rejected because it would duplicate quality logic across consumers.
