# CI/CD Strategy

Milestone 1 defines validation workflows only. No staging or production deployment is configured.

## Pull-Request Validation

Pull requests will run Python linting, formatting checks, mypy, pytest, repository validation, and R project validation where R tooling is available. PRs must identify the milestone, document tests, and confirm no sensitive data or credentials were added.

## Merge to Main

Pushes to `main` run the same validation checks. Later milestones may publish build artefacts, but deployment will remain separate from build validation.

## Staging and Production Targets

Staging deployment is a future target. Production release will require tags or manual approval, smoke testing, evidence capture, rollback planning, and no direct feature-branch production deployment.

## Rollback and Evidence

Future releases must retain enough evidence to identify the approved model, service version, configuration, and monitoring state. Milestone 1 documents the strategy but does not deploy.
