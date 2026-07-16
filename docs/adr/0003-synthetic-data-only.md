# ADR 0003: Synthetic Data Only

## Status

Accepted for Milestone 1.

## Context

The scenario is healthcare operational decision support, which would be sensitive with real data. The repository must be safe to run, review, and share without exposing patient or operational records.

## Decision

Only synthetic data may be used. Real patient data, NHS data, HMRC data, credentials, and sensitive operational data are prohibited.

## Consequences

Future modelling evidence will demonstrate engineering and governance practice, not real-world clinical validity. Validation must include checks for generated artefacts and obvious secrets.

## Alternatives Considered

Using de-identified real data was rejected because it still creates governance risk. Using public healthcare data was rejected because the target product needs controlled synthetic contracts.
