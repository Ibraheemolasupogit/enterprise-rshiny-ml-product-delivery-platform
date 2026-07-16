# ADR 0013: Training-Only Preprocessing Fit

Status: Accepted

## Context

Imputation values, scaling statistics, and category vocabularies can leak validation or test information if fitted globally.

## Decision

Milestone 5 fits preprocessing state only on training rows. Validation and test rows are transformed using the train-fitted medians, modes, means, standard deviations, and categorical vocabularies.

## Consequences

Unknown categories in validation or test are ignored rather than refitting the vocabulary. The preprocessing artefact is metadata-only and is explicitly not a predictive model.

## Alternatives Considered

Fitting preprocessing on the full dataset was rejected as leakage. Adding a machine-learning pipeline dependency was rejected because no predictive estimator is needed yet.
