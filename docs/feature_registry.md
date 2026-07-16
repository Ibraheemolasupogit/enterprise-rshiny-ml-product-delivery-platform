# Feature Registry

The feature registry is generated for every transformed output column. Each entry maps the output feature to a source column or derivation, transformation, prediction-time availability, and leakage status.

Numeric source predictors are median-imputed and standard-scaled using training-split statistics. Categorical predictors are mapped to train-fitted one-hot columns. Boolean predictors are mode-imputed using the training split. Missingness indicator columns are registered as derived features tied to the source column that produced them.

The machine-readable registry is `reports/model_evaluation/feature_registry.json`. It includes the registry entry count, output feature count, coverage result, stable ordering result, and ordered entries. Repository validation requires the registry count to match the transformed feature count and requires coverage to be valid.

This registry is not a model card and does not describe predictive performance. It is a feature-contract artefact that allows future Milestone 6 model development to consume a stable, auditable feature schema without reinterpreting admission-time availability or leakage status.
