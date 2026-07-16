# Testing Strategy

Milestones 1, 2, 3, 5, 6, and 7 implement foundation, synthetic-source, local database, feature-engineering, model-development, registry, governance, and local serving checks. Tests include Python unit tests, synthetic-data module tests, database build tests, logical-view client tests, feature configuration tests, leakage checks, patient-group split checks, training-only preprocessing tests, model configuration tests, baseline tests, candidate training tests, registry state tests, approval-gate tests, serving schema tests, authentication tests, readiness tests, rollback tests, CLI integration tests, SQL contract tests, repository structure checks, manifests, evidence validation, feature registry coverage, model-card checks, and data dictionary coverage, plus minimal R project-foundation tests.

Milestone 6 validation now requires successful XGBoost import, native fit, pipeline training, candidate artefact creation, validation metrics, comparison inclusion, calibration handling, explainability evidence, and reproducibility checks. A `failed_local_dependency` XGBoost status is no longer accepted as complete Milestone 6 evidence.

## Python Unit Testing

Python tests validate package import, version exposure, settings loading, environment override behaviour, repository path resolution, governed source loading, admission-time temporal derivations, deterministic splitting, preprocessing state, feature output contracts, and reproducibility scripts.

## R Testing

R `testthat` tests now validate the R-Shiny MVP configuration, prediction contract, API response parsing, review-mode banner behaviour and feedback contract. A bounded R-to-FastAPI smoke test validates review-mode prediction through the documented API.

## Configuration and Structure Validation

Configuration tests verify YAML syntax, required version fields, supported integration modes, and absence of obvious credentials. Repository-structure tests verify required directories, documentation, and absence of generated datasets or models.

## Future Test Layers

Advanced R-Shiny, monitoring, deployment, and UAT checks will be expanded in later milestones. Milestone 9 deliberately stops at overview, single prediction and feedback; it does not approve, activate, deploy, monitor, retrain or implement cohort scoring.
## Milestone 10 R-Shiny Tests

Milestone 10 adds batch contract tests, batch API parser tests, export tests, locked evidence tests, governance read-only tests, and browser-backed `shinytest2` navigation coverage. The quality target also runs single and batch FastAPI smoke tests in local review mode.

Browser-backed tests must genuinely run; skipped browser tests do not satisfy Milestone 10 completion.
## Release Assurance Tests

Milestone 13 adds workflow contract tests, container contract tests, release configuration tests, release readiness tests, release inventory tests, and assurance evidence contract tests. Local smoke testing validates default governed mode and explicit review mode without external deployment.
