# ADR 0012: Temporal Patient-Group Splitting

Status: Accepted

## Context

The synthetic source can include multiple admissions per patient. Random row-level splits would allow the same patient to appear across train, validation, and test, creating contamination risk.

## Decision

Milestone 5 sorts patients by first admission datetime and assigns whole patient groups to train, validation, and test using deterministic 60/20/20 targets.

## Consequences

Patient overlap is zero and reproducible. Chronological row boundaries are approximate because patient grouping takes priority in a small synthetic dataset.

## Alternatives Considered

Pure chronological row splitting was rejected because it can split repeat patients. Random splitting was rejected because it weakens temporal evaluation and contamination controls.
