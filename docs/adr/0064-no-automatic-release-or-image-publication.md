# ADR 0064: No Automatic Release Or Image Publication

Status: Accepted

Context: Milestone 13 validates delivery mechanics but does not authorize external distribution.

Decision: Workflows build local artefacts and CI artefacts only. They do not push images, create GitHub releases, tag commits, or publish packages.

Consequences: Release readiness can be reviewed manually without creating external artefacts. Future release publication must be implemented under a separate milestone.

Alternatives considered: Automatic release on `main` was rejected because it would outrun governance review.
