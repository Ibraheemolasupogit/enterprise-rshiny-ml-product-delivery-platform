# MVP Scope

## MVP Capabilities

The future MVP will include deterministic synthetic source systems, a governed logical data layer, validation checks, feature engineering, a baseline model, a local model registry, FastAPI scoring, a modular R-Shiny decision-support interface, feedback capture, monitoring, and controlled retraining documentation.

## MVP Exclusions

The MVP excludes real patient data, real NHS or HMRC integrations, automated clinical decisions, direct production deployment from feature branches, fabricated Denodo evidence, fabricated SAS Viya evidence, and automatic model promotion.

## Acceptance Criteria

Each milestone must pass local validation, preserve synthetic-data boundaries, update documentation, include appropriate tests, and avoid implementing later milestones early. User-facing functionality must be supported by acceptance criteria, UAT evidence, and operational handover artefacts.

## Dependencies

Later MVP work depends on the Milestone 1 repository foundation, deterministic synthetic data generation, clear contracts, and stable service boundaries between Python, SQL, and R-Shiny components.

## Risks

Primary risks include scope creep, false completion claims, weak governance evidence, insufficient test coverage, and commercial-tool references that imply capabilities not implemented.

## Definition of Done

Milestone 1 is done when the repository foundation, documentation, config, validation, tests, and CI definitions are present and local checks have been attempted.
