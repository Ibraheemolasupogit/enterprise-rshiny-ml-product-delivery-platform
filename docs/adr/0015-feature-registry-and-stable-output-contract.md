# ADR 0015: Feature Registry and Stable Output Contract

Status: Accepted

## Context

Future model development needs reproducible feature columns, ordering, and transformation metadata. Generated feature datasets remain ignored, so small committed evidence must carry the contract.

## Decision

Milestone 5 generates a feature registry covering every transformed column, plus stable manifests and checksums for feature, target, and identifier outputs.

## Consequences

Feature outputs can be rebuilt without committing generated datasets. Future model work can compare expected feature names and order before training.

## Alternatives Considered

Committing generated feature Parquet files was rejected because they are build artefacts. Leaving feature schema implicit in code was rejected because it makes downstream contracts brittle.
