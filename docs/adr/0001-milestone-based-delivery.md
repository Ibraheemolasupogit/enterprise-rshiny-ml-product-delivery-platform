# ADR 0001: Milestone-Based Delivery

## Status

Accepted for Milestone 1.

## Context

The product covers many capabilities: R-Shiny, Python machine learning, SQL, governed data access, FastAPI, testing, CI/CD, monitoring, retraining, governance, and handover. Implementing everything at once would make it hard to validate scope and claims.

## Decision

The repository will be delivered milestone by milestone. Milestone 1 contains foundation work only. Later milestones must not be implemented early.

## Consequences

Scope is easier to review, evidence can be attached to each phase, and accidental false completion claims can be caught by validation.

## Alternatives Considered

A single large scaffold was rejected because it would invite placeholder functionality. A model-first build was rejected because the product lifecycle is broader than modelling.
