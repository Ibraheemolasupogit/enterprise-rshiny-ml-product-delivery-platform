# End-to-End Lineage

This lineage narrative traces the committed synthetic demonstration from source data to review-mode product evidence. It uses actual repository concepts and paths. It does not fabricate live external identifiers.

## Source Data

- Source type: deterministic synthetic healthcare data.
- Source version: `0.2.0` in `data/sample/generation_manifest.json`.
- Datasets: `patients`, `admissions`, `diagnoses`, `ward_capacity`, `workforce`, `outcomes`.
- Contracts: `config/data_contracts.yaml`, `docs/data_dictionary.md`, `tests/contract/test_synthetic_schemas.py`.

## Datastore And Governed Views

- Local default datastore: DuckDB configured by `config/database.yaml`.
- PostgreSQL foundation: `docker-compose.postgresql.yml`, `database/postgresql/migrations`, `src/ml_product/ingestion/postgresql.py`.
- Denodo governed view path: `database/denodo/vql`, `src/ml_product/ingestion/denodo_client.py`.
- Governed model-source contract: `curated.model_source_view`.
- Eligible model-source population: `117` rows, recorded by the lifecycle package source contract.

## Feature Lineage

- Feature source provider: `denodo_compatible_local` in `config/features.yaml`.
- Feature build evidence: `reports/model_evaluation/feature_build_manifest.json`.
- Feature dataset version: `0.5.0`.
- Source fingerprint: `a420857558b5de7ae92167c6ce58a2afe609810ae7c8d38f0605be6394f05509`.
- Leakage controls: `reports/model_evaluation/leakage_report.json`, `docs/target_leakage_controls.md`.

## Model Lineage

- Training configuration: `config/model_training.yaml`.
- Candidate evidence: `reports/model_evaluation/model_training_manifest.json`, `reports/model_evaluation/model_comparison.json`.
- Candidate identifiers:
  - Logistic regression: `CAND-52A549C43FF82D08`.
  - Random forest: `CAND-22810BAD2859A9DB`.
  - XGBoost: `CAND-85EA9202CAD6FE7F`.
- Selected candidate: XGBoost, candidate `CAND-85EA9202CAD6FE7F`.
- Calibration and threshold evidence: `reports/model_evaluation/calibration_report.json`, `reports/model_evaluation/threshold_analysis.json`.
- Fairness evidence: `reports/model_evaluation/fairness_summary.json`.

## Registry And Lifecycle Lineage

- Local registry: `models/registry.json`.
- Registry manifest: `reports/model_evaluation/model_registry_manifest.json`.
- Registry version: `1`.
- Approval status: `pending` in `reports/model_evaluation/approval_decision.json`.
- Activation status: `inactive` in `reports/model_evaluation/activation_status.json`.
- Model lifecycle package fingerprint: `4dfd09c5192cce17e86144a6367909350b2a574d43652ca4253947f9d41d9525`.
- Registration fingerprint: `96f00a2ecc3570a9344eda3dded563262fc415ac4d9a58d7684e7b1bd49ce0a5`.
- External SAS Viya identifiers: unavailable unless a live SAS Viya environment performs registration. No live external ids are committed or invented.

## Promotion And Activation Lineage

- Promotion assessment code: `src/ml_product/lifecycle/promotion.py`.
- Lifecycle orchestration code: `src/ml_product/lifecycle/orchestration.py`.
- Promotion decision today: blocked unless required external registration, reconciliation and governance approval exist.
- Local active-model identity: none. The registered candidate is inactive.
- Boundary: external promotion does not activate the local model; local activation is an explicit existing registry action.

## Monitoring And Release Lineage

- Monitoring baseline manifest: `reports/monitoring/monitoring_baseline_manifest.json`.
- Monitoring review evidence: `reports/monitoring/monitoring_review.json`.
- Retraining recommendation: `reports/retraining/retraining_recommendation.json`, currently review-only with no automatic action.
- Release readiness: `reports/assurance/release_readiness.json`.
- Local review readiness: `ready_for_local_review`.
- Operational release readiness: `blocked_for_operational_release`.

## Summary

The lineage is complete for a synthetic, local-review portfolio product. PostgreSQL and Denodo provide enterprise data-access foundations; SAS Viya lifecycle workflows are provider-compatible and mock-tested; live SAS Viya identifiers require a real external environment.
