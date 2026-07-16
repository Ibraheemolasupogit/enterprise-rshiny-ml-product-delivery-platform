# ADR 0002: Python and R Service Boundary

## Status

Accepted for Milestone 1.

## Context

The target product combines Python model lifecycle components with a modular R-Shiny operational application. Clear boundaries are needed for testing, ownership, and future deployment.

## Decision

Python will own configuration validation, synthetic data generation, validation, modelling, registry, serving, monitoring, and retraining code. R-Shiny will own user-facing operational workflows and R-specific tests. FastAPI will later provide the service boundary between model scoring and the R-Shiny application.

## Consequences

The repository can support Python and R specialists while preserving separation of concerns. Integration contracts will be needed before R-Shiny consumes scoring outputs.

## Alternatives Considered

An all-R implementation was rejected because the brief requires Python machine learning and FastAPI. An all-Python UI was rejected because the planned product is R-Shiny.
