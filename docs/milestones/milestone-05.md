# Milestone 5 — Feature Engineering

Status: Complete

Milestone 5 implements reproducible feature engineering and deterministic dataset splitting for the admission-time long-stay prediction contract. The pipeline reads only `curated.model_source_view` through the governed logical-view client, derives admission-time temporal features, applies eligibility controls, checks leakage rules, splits by temporal patient groups, fits preprocessing only on the training split, and writes train, validation, and test feature outputs.

Generated datasets are ignored under `data/processed/features`. Committed evidence is stored under `reports/model_evaluation` and includes the build manifest, feature registry, split summary, exclusion summary, leakage report, preprocessing metadata, and feature build report.

No model training, model registry, FastAPI service, R-Shiny behaviour, monitoring, retraining, deployment, SAS Viya integration, or real Denodo integration is included in this milestone.
