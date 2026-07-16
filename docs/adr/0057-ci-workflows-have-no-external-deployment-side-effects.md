# ADR 0057: CI Workflows Have No External Deployment Side Effects

Status: Accepted

Context: Milestone 13 needs CI/CD assurance before the repository has a first commit or remote CI history. Deployment-capable workflows would create risk before governance is complete.

Decision: Workflows validate, build, scan, and upload CI artefacts only. They do not deploy, publish images, create releases, create tags, approve models, activate models, or trigger retraining registration.

Consequences: Release confidence improves while external environments remain untouched. A later milestone must add deployment only after approval controls exist.

Alternatives considered: A single deploy workflow was rejected because it could imply operational readiness.
