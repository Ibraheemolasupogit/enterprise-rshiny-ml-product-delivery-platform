# Data Lineage

```text
Milestone 2 files
        |
raw tables
        |
staged tables
        |
quality reconciliation
        |
curated views
        |
feature engineering
        |
ignored feature datasets and committed feature evidence
        |
candidate model development evidence
```

`curated.patient_admission_view` uses staged patients and admissions. `curated.admission_diagnosis_summary` uses staged diagnoses after orphan exclusion. `curated.daily_ward_operational_context` uses ward capacity and workforce. `curated.admission_operational_context` joins admissions to same-day ward context. `curated.outcome_context_view` preserves source and governed outcome fields. `curated.model_source_view` joins governed source context for Milestone 5 feature engineering.

Milestone 5 records source view, source fingerprint, database build identifier, configuration fingerprint, split fingerprint, output checksums, and feature registry entries in `reports/model_evaluation`. Outcome and discharge columns remain reference fields and are not predictor lineage.

Milestone 6 starts from the Milestone 5 feature artefacts and evidence only. It records training configuration fingerprints, candidate identifiers, validation metrics, locked test metrics, calibration, explainability, fairness, and recommendation evidence in `reports/model_evaluation`.

Milestone 7 registers the selected candidate in a local filesystem registry. It records registry version, candidate identifier, artefact checksum, preprocessor checksum, feature build identifier, approval state, activation state, serving contract, and audit summary. Registration remains local and does not imply approval or deployment.

Milestone 9 adds R-Shiny as an API client only. Single-record prediction lineage flows from Shiny form inputs to FastAPI validation, registry-compatible preprocessing and local review-mode scoring. Shiny does not read model artefacts or DuckDB tables directly.
## R-Shiny Cohort Lineage

Milestone 10 cohort scoring uses synthetic CSV upload to R validation, then FastAPI `/v1/predict/batch`, then bounded Shiny result presentation and optional CSV export. Uploads are not retained and exports exclude raw inputs, identifiers, outcomes, model artefact paths, and hidden transformed features.
## Release Inventory

Milestone 13 release inventory excludes generated datasets, DuckDB files, model binaries, coverage artefacts, browser artefacts, local logs, secrets, and temporary caches. Registry metadata and committed evidence remain eligible for the first controlled commit.
