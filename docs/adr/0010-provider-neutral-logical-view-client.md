# ADR 0010: Provider-Neutral Logical View Client

## Status

Accepted for Milestone 3.

## Context

The local logical layer should be replaceable by real Denodo later.

## Decision

Define a provider-neutral logical-view client with a DuckDB implementation and an explicitly unimplemented Denodo boundary.

## Consequences

Future adapters can preserve the same consumer interface. Arbitrary SQL remains disabled.

## Alternatives Considered

Hard-coding DuckDB queries in consumers was rejected because it would make future adapters harder.
