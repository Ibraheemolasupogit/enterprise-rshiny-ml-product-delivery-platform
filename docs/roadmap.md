# Roadmap

| Milestone | Objective | Principal deliverables | Dependencies | Exit criteria | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Product foundation | Structure, docs, config, tests, CI definitions | None | Local validation attempted | Complete |
| 2 | Deterministic synthetic source systems | Synthetic generators and fixtures | 1 | Reproducible synthetic data | Complete |
| 3 | Governed data layer | Local schemas and logical views | 2 | Contracts and views validated | Complete |
| 4 | Denodo integration | Optional real integration when genuine access exists | 3 | Evidence and honest mode labels | Externally blocked |
| 5 | Feature engineering | Tested feature pipelines | 3 | Feature contracts pass | Complete |
| 6 | Model development | Baseline model and evaluation | 5 | Model evidence produced | Complete |
| 7 | Registry and serving | Registry and FastAPI service | 6 | Local registry and fail-closed API implemented | Complete |
| 8 | SAS Viya integration | Genuine SAS Viya lifecycle evidence | 6 | Real access and evidence required | Externally blocked |
| 9 | R-Shiny MVP | Local review-mode Shiny API client | 7 | UAT-ready MVP | Complete |
| 10 | Advanced R-Shiny capabilities | Richer workflows and feedback | 9 | Extended UAT passes | Complete |
| 11 | Monitoring and drift | Monitoring reports and alerts | 7 | Drift checks documented | Complete |
| 12 | Retraining governance | Controlled retraining workflow | 11 | Human approval workflow documented | Complete |
| 13 | CI/CD and deployment | Safe build and deployment flow | 9 | Staging and release controls pass | Planned |
| 14 | Handover and portfolio evidence | Runbooks and operating evidence | All prior | Handover package complete | Planned |
## Current Milestone Status

Milestone 1 - Complete
Milestone 2 - Complete
Milestone 3 - Complete
Milestone 4 - Externally blocked
Milestone 5 - Complete
Milestone 6 - Complete
Milestone 7 - Complete
Milestone 8 - Externally blocked
Milestone 9 - Complete
Milestone 10 - Complete
Milestone 11 - Complete
Milestone 12 - Complete
Milestones 13-14 - Planned

Next recommended milestone: Milestone 13 - CI/CD and deployment controls.
## Milestone 13

CI/CD architecture, container packaging, security and dependency assurance, SBOM manifests, local deployment smoke validation, and release gates are implemented locally. Remote CI remains pending until the first commit and push. Milestone 14 deployment automation remains planned, not implemented.
