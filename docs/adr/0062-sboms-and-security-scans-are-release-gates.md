# ADR 0062: SBOMs And Security Scans Are Release Gates

Status: Accepted

Context: Delivery assurance needs more than functional tests. Dependencies, containers, secrets, and filesystem contents must be inspected before release.

Decision: Secret scanning, dependency audit, static analysis, container scanning, Dockerfile linting, and SBOM generation are release assurance gates. Missing local tools are recorded honestly and configured for CI.

Consequences: Security evidence becomes auditable, but it remains bounded and does not claim complete security assurance.

Alternatives considered: Advisory-only scans were rejected for secrets and high-impact findings.
