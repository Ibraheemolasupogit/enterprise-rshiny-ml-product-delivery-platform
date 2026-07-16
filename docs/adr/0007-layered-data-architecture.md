# ADR 0007: Layered Data Architecture

## Status

Accepted for Milestone 3.

## Context

Source values, typed tables, quality evidence, metadata, and consumer views need separation.

## Decision

Use `raw`, `staged`, `quality`, `metadata`, and `curated` schemas.

## Consequences

Quality treatment is explicit and consumers avoid raw source tables.

## Alternatives Considered

A single schema was rejected because it hides governance boundaries.
