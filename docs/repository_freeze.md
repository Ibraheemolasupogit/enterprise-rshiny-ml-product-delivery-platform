# Repository Freeze Guidance

Milestone 15.6 freezes the portfolio for interview review. The goal is to prove a clean checkout can reconstruct generated review artifacts, run offline-safe assurance, and explain any external limitations honestly.

## Complete

- Synthetic healthcare source data, contracts and quality controls.
- DuckDB local data build and PostgreSQL production-oriented foundation.
- Denodo governed virtual-view integration path.
- Leakage-safe feature engineering.
- Python model training, evaluation, calibration, thresholding, fairness and explainability.
- Local registry, approval, activation and rollback boundaries.
- SAS Viya-compatible lifecycle package, registration, reconciliation and promotion workflows with offline/mock validation.
- FastAPI review serving and R Shiny review product.
- Monitoring, controlled retraining review, release assurance and canonical lifecycle orchestration.
- Interview architecture, lineage, evidence index and demo guide.

## Optional External Validation

PostgreSQL and Denodo live checks are optional for final portfolio review and can be enabled locally when services are available. Live SAS Viya registration and promotion require an available SAS Viya environment and must not be fabricated.

## Freeze Rules

- Do not add new product features before interviews.
- Do not approve, promote, activate, deploy or roll back the model for convenience.
- Do not make PostgreSQL, Denodo or SAS Viya mandatory for CI.
- Do not commit generated runtime workflow evidence unless it is part of documented assurance output.
- Do not update remote CI evidence until genuine GitHub Actions runs exist.

## Clean-Checkout Command

Use the canonical offline assurance command:

```bash
make final-assurance
```

This reconstructs review artifacts, runs offline-safe validation, writes `reports/assurance/final_assurance.json`, validates lifecycle orchestration evidence, and confirms operational release remains blocked.

Optional live checks:

```bash
python3 scripts/final_assurance.py --include-live
python3 scripts/final_assurance.py --include-containers
python3 scripts/final_assurance.py --include-r
```

## Demo Prerequisites

- Python development dependencies installed with `python3 -m pip install -e ".[dev]"`.
- R and Docker are optional for the short interview path.
- PostgreSQL, Denodo and SAS Viya are optional external-service paths and should be described by status, not implied as mandatory.

## Troubleshooting

- Missing generated model or monitoring artifacts: run `make build-review-artifacts`.
- Documentation contract failure: run `python3 scripts/validate_repository.py --docs`.
- Lifecycle evidence issue: run `make lifecycle-e2e-local` then `make lifecycle-e2e-validate`.
- Release-readiness mismatch: run `make release-assurance`.
- Generated runtime noise: run `make clean` and remove ignored local outputs before preparing a final diff.
