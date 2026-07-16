# Product Backlog

| ID | Epic | User story | Priority | Acceptance criteria | Dependencies | Target milestone | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PF-001 | Product foundation | As a product team, we need a clear repository foundation. | High | Root files, structure, docs, config, tests, and CI definitions exist. | None | 1 | Complete |
| PF-002 | Product foundation | As QA, I need repository validation. | High | Validation script and tests fail clearly on missing foundation assets. | PF-001 | 1 | Complete |
| SS-001 | Synthetic source systems | As a data engineer, I need deterministic synthetic sources. | High | Synthetic data generation is reproducible and documented. | PF-001 | 2 | Complete |
| GL-001 | Governed data layer | As an analyst, I need governed logical views. | High | Local SQL-compatible views pass contracts. | SS-001 | 3 | Complete |
| DEN-001 | Denodo integration | As governance, I need honest Denodo labelling. | Medium | Genuine access is required for real evidence; no fake evidence is produced. | GL-001 | 4 | Externally blocked |
| FE-001 | Feature engineering | As a data scientist, I need tested features. | High | Feature pipelines trace to contracts. | GL-001 | 5 | Complete |
| MD-001 | Model development | As a data scientist, I need baseline model evidence. | High | Candidate models are trained on synthetic features and evaluated. | FE-001 | 6 | Complete |
| RS-001 | Registry and serving | As platform support, I need controlled serving. | High | Local registry and FastAPI fail-closed serving implemented. | MD-001 | 7 | Done |
| SAS-001 | SAS Viya integration | As governance, I need honest SAS Viya evidence. | Medium | Genuine SAS Viya activity is evidenced without local substitution. | MD-001 | 8 | Externally blocked |
| SH-001 | R-Shiny MVP | As an operational user, I need a usable decision-support view. | High | R-Shiny MVP supports overview, single synthetic prediction and feedback through FastAPI review mode. | RS-001 | 9 | Done |
| SH-002 | Advanced R-Shiny capabilities | As users, we need richer review and feedback. | Medium | Additional modules meet UAT criteria. | SH-001 | 10 | Done |
| MON-001 | Monitoring and drift | As service support, I need health evidence. | High | Monitoring reports and alerts are reproducible. | RS-001 | 11 | Done |
| RT-001 | Retraining governance | As governance, I need controlled retraining. | High | Retraining requires review and human approval. | MON-001 | 12 | Done |
| CICD-001 | CI/CD and deployment | As platform engineering, I need safe releases. | High | Build and deployment are separated with approval gates. | SH-001 | 13 | Planned |
| HO-001 | Handover and portfolio evidence | As support, I need operational documentation. | High | Runbooks, guides, and limitations are complete. | All prior | 14 | Planned |
## Milestone 10 Completion

Advanced R-Shiny product scope is complete locally: synthetic cohort scoring, model performance evidence, model governance display, error handling, accessibility improvements, exports, UAT evidence, and browser-backed test coverage.

## Milestone 11 Completion

Monitoring and drift scope is complete locally: deterministic synthetic monitoring baseline, current-window fixtures, data-quality checks, feature drift, prediction drift, labelled performance monitoring, calibration checks, operational evidence, review-only alerts, R-Shiny monitoring display, tests and documentation.

## Milestone 12 Completion

Controlled retraining review is complete locally: eligibility checks, governed labelled dataset preparation, champion-challenger comparison, fairness and stability review, promotion gates, recommendation evidence, and a read-only R-Shiny review page. The milestone does not approve, activate, deploy or replace a model.
## Milestone 13

- Add focused CI workflow definitions: done.
- Add local container packaging for API and R-Shiny: done.
- Add release assurance gates and evidence: done.
- Validate local-only deployment modes: done.
- Push initial commit and review remote CI: deferred manual step.
