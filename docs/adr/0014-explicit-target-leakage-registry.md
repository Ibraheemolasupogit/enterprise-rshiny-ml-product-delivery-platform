# ADR 0014: Explicit Target-Leakage Registry

Status: Accepted

## Context

The governed model source contains useful reference and outcome fields that must not become predictors. Documentation alone is not sufficient to prevent accidental leakage.

## Decision

Milestone 5 stores prohibited predictors in configuration and checks feature names for target, length-of-stay, discharge, readmission, outcome, and identifier leakage before outputs are written.

## Consequences

The committed leakage report provides machine-readable evidence. Future milestones can extend the prohibited registry as new fields appear.

## Alternatives Considered

Relying on manual review was rejected. Removing all outcome fields from the source view was rejected because they are needed for target construction, evaluation, and lineage.
