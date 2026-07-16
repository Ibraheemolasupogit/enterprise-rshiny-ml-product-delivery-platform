# Milestone 6 — Model Development

Status: Complete

Milestone 6 implements deterministic candidate model development using the leakage-controlled Milestone 5 feature datasets. It trains prevalence and majority baselines, logistic regression, Random Forest, and XGBoost. It produces validation-led comparison, calibration, threshold selection, locked test evaluation, explainability, fairness evidence, a model-development report, and a model card.

The XGBoost remediation resolved a local macOS OpenMP blocker (`libomp.dylib` missing for the official XGBoost wheel). After installing Homebrew `libomp`, the configured CPU, single-threaded XGBoost candidate trained through the real pipeline and regenerated Milestone 6 evidence.

The selected candidate remains unregistered and unserved. Candidate binaries are ignored under `models/candidate`; committed evidence is under `reports/model_evaluation`.

No Milestone 7 registry, FastAPI serving, R-Shiny behaviour, monitoring, retraining, SAS Viya integration, Denodo integration, deployment, approval, or external service registration is implemented.
