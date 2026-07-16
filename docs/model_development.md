# Model Development

Milestone 6 trains deterministic candidate models using only Milestone 5 transformed feature outputs. It does not query raw tables, curated views, Denodo, or the DuckDB database during modelling. Preprocessing is not refitted; all candidates consume the stable 71-column feature contract from `data/processed/features`.

The configured experiment is `long_stay_admission_risk` with seed `20260714`. Candidate families are prevalence baseline, majority-class baseline, logistic regression, Random Forest, and XGBoost. Logistic regression and Random Forest use fixed configured hyperparameters. XGBoost is configured through the official Python package, single-threaded CPU settings, and fixed hyperparameters.

On macOS development machines, the official XGBoost wheel requires a compatible OpenMP runtime. The local blocker was a missing `libomp.dylib`; it was corrected by installing Homebrew `libomp`, after which XGBoost import, native fit, and pipeline training passed. Homebrew is not a deployed product dependency.

Validation data is used for calibration, threshold selection, and candidate recommendation. The test set is evaluated only after the model, calibration method, and threshold are locked. Candidate artefacts are written under ignored `models/candidate`; committed evidence is written under `reports/model_evaluation`.

No model registration, production promotion, FastAPI serving, R-Shiny integration, monitoring, retraining, SAS Viya integration, Denodo integration, or deployment is implemented in Milestone 6.
