# Interview Demonstration Guide

Use this script for a 10-15 minute walkthrough. Do not rebuild every artifact or run the full test suite during the interview.

## 0-2 Minutes: Architecture

Command:

```bash
sed -n '1,220p' docs/interview_architecture.md
```

Expected output: the business problem, architecture sections and mode boundaries.

Explain that the product is synthetic healthcare operations evidence for long-stay risk review. Point to [docs/diagrams/interview-architecture.mmd](diagrams/interview-architecture.mmd) for the data, control and evidence planes.

Fallback: if terminal rendering is poor, open the Markdown files in GitHub.

## 2-4 Minutes: Governed Data Path

Commands:

```bash
python3 -m ml_product.cli describe-sample-data --config config/synthetic_data.yaml
python3 -m ml_product.cli list-logical-views --config config/database.yaml
```

Expected output: synthetic dataset summaries and governed curated logical views including `curated.model_source_view`.

Explain that DuckDB is the default local path, PostgreSQL is the production datastore foundation, and Denodo provides governed virtual-view access when live integration is enabled.

Optional live Denodo evidence:

```bash
make denodo-ready
make denodo-list-views
make denodo-compare-postgresql
```

Fallback: if Docker or Denodo is unavailable, show `docs/denodo_integration.md`, `database/denodo/vql/030_governed_virtual_views.vql` and `tests/integration/test_denodo_integration.py`.

## 4-6 Minutes: Model Evidence

Commands:

```bash
python3 -m ml_product.cli compare-models --config config/model_training.yaml
python3 -m ml_product.cli show-candidate-recommendation --config config/model_training.yaml
```

Expected output: validation-led comparison and XGBoost recommendation for registration review.

Explain leakage controls, validation-only model selection, calibration, threshold selection and fairness caveats. Emphasise that synthetic evidence supports review, not approval.

## 6-9 Minutes: Lifecycle Controls

Commands:

```bash
python3 -m ml_product.cli lifecycle-show-champion
python3 -m ml_product.cli lifecycle-compare-champion
python3 -m ml_product.cli lifecycle-assess-promotion --dry-run
python3 -m ml_product.cli lifecycle-run-end-to-end --mode local_safe
python3 -m ml_product.cli lifecycle-run-end-to-end --mode enterprise_dry_run --dry-run
```

Expected output: no active champion or a blocked promotion assessment, with workflow status `blocked` rather than `failed`.

Explain the blocked governance gates:

- candidate is not approved
- local activation is inactive
- external promotion is separate from local activation
- SAS Viya live registration and promotion require an external environment

Fallback: if generated review artifacts are missing, run `make build-review-artifacts` before the lifecycle commands or show `docs/lifecycle_orchestration_demo.md`.

## 9-12 Minutes: Product Interface

Commands:

```bash
make validate-serving
docker compose -f docker-compose.yml -f docker-compose.review.yml up --build
```

Expected output: serving validation passes for the configured review boundary; Docker Compose starts the API and R Shiny review stack when Docker is available.

Explain that operational serving fails closed without approved active model state, while review mode is labelled and bounded.

Fallback: if Docker is unavailable, show `docs/rshiny_user_guide.md`, `docs/rshiny_model_governance.md` and `reports/uat/rshiny_advanced_manifest.json`.

## 12-14 Minutes: Monitoring And Release Evidence

Commands:

```bash
python3 -m ml_product.cli describe-monitoring --config config/monitoring.yaml
python3 -m ml_product.cli assess-release-readiness --config config/release.yaml
```

Expected output: monitoring summary and release readiness showing local review readiness but operational release blocked.

Explain that monitoring and retraining are review workflows. They do not approve, activate, promote, roll back or deploy a model.

## Closing Summary

Close with:

- The repository demonstrates an end-to-end ML product, not just a notebook.
- Data, model, lifecycle, serving, monitoring and release evidence are separated.
- PostgreSQL and Denodo show the enterprise data-access path.
- SAS Viya is treated as an optional lifecycle provider, not the modelling engine.
- Governance blocks remain visible and intentional.
- The project is interview-ready without claiming real deployment or live SAS Viya validation.
