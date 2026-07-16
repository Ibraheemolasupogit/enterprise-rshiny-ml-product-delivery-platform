# R-Shiny Architecture

```text
R-Shiny browser session
        ↓
R API client
        ↓
FastAPI authentication and validation
        ↓
Registry and serving compatibility checks
        ↓
Registered XGBoost candidate in local review mode
```

Shiny does not load model files directly, does not call Python through `reticulate`, and does not query DuckDB for prediction. All scoring requests use the documented FastAPI contract.

The only implemented product pages are Product Overview, Single Prediction and User Feedback. Later product pages remain disabled in `config/rshiny.yaml`.
## Milestone 10 Advanced Architecture

The Shiny product has six pages: Overview, Single Prediction, Cohort Scoring, Model Performance, Model Governance, and Feedback. Single and cohort scoring call FastAPI only. Cohort uploads are parsed and validated in R, then sent to `/v1/predict/batch`; uploads are not retained.

Performance and governance views read committed evidence files from `reports/model_evaluation` and fail closed if required state is inconsistent. No monitoring, drift detection, retraining, approval, activation, rollback, or deployment controls are part of this architecture.
