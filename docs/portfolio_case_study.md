# Portfolio Case Study

This project is a governed end-to-end ML product delivery platform built on synthetic healthcare data. It demonstrates how a product team can move from source-system modelling through data quality, feature engineering, model development, serving, R-Shiny product workflows, monitoring, controlled retraining, CI/CD and release assurance without claiming real clinical impact.

## Problem And Users

The product simulates long-stay admission risk review for operational and analytics users. The intended users are data scientists, analytics engineers, product owners, governance reviewers and R-Shiny consumers who need a transparent local-review product rather than an ungoverned notebook.

## Technical Flow

Synthetic source systems feed DuckDB raw, staged, quality, metadata and curated layers. A provider-neutral logical layer keeps the local implementation compatible with a future Denodo adapter, while Denodo itself remains externally blocked. Feature engineering uses temporal patient-group splitting and training-only preprocessing to reduce leakage. XGBoost is the recommended candidate, calibrated with sigmoid calibration and selected by validation-only rules; weak locked-test performance remains visible.

## Product And Governance

FastAPI owns scoring and fails closed without an approved active model. R-Shiny consumes FastAPI rather than model files and exposes overview, single prediction, cohort scoring, performance, monitoring, retraining review and governance views. Local review mode is explicit and not operational. Registry version 1 is pending approval and inactive. Monitoring is review-only, and controlled retraining recommends `retain_champion` with no automatic action.

## CI/CD, Security And Release

Milestone 13 added GitHub Actions, container packaging, local Docker Compose validation, SBOM and release gates. Milestone 14 adds portfolio assurance, final evidence, controlled first commit and genuine remote CI validation. Operational release remains blocked by missing approval, inactive model state, no external deployment target and no deployment approval.

## Commercial Boundaries

Denodo and SAS Viya are documented future integrations, not fabricated evidence. The local logical and governance layers are implemented; commercial screenshots or execution claims are intentionally absent.

## Interview Talking Points

- Built a full product lifecycle rather than a single model artifact.
- Preserved approval and activation gates even when local review mode works.
- Kept weak evidence visible instead of polishing metrics.
- Used synthetic-only evidence and documented external blockers honestly.
