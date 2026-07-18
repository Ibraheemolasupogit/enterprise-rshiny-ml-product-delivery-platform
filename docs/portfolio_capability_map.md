# Portfolio Capability Map

| Role or capability | Repository evidence |
| --- | --- |
| Data scientist | Model training, calibration, thresholding, fairness and explainability in `src/ml_product/modelling`; evidence in `reports/model_evaluation`. |
| ML engineer | Feature pipeline, model package, registry integration, FastAPI serving and lifecycle orchestration in `src/ml_product`. |
| MLOps engineer | GitHub Actions workflows, Dockerfiles, release gates, SBOM/security evidence and Makefile validation targets. |
| Analytics engineer | DuckDB, PostgreSQL, Denodo VQL, governed views and logical-view contracts in `database`, `config/database.yaml` and `src/ml_product/ingestion`. |
| Data platform engineer | PostgreSQL Docker Compose, migrations, readiness checks and Denodo mapping docs. |
| Technical architect | Data plane, control plane, evidence plane, mode boundaries and mutation controls in `docs/interview_architecture.md`. |
| Healthcare analytics | Synthetic admission long-stay risk use case, operational decision context and data dictionary. |
| Model risk and governance | Registry, approval, activation, promotion, rollback, monitoring, retraining and release-readiness evidence. |

This project is strongest as a demonstration of governed ML product delivery. It does not claim clinical deployment, patient-outcome evidence or live SAS Viya execution.
