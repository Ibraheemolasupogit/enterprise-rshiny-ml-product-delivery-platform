# Security Scanning

Security assurance is layered. Secret scanning is blocking. Python static analysis uses Bandit. Python dependency audit uses pip-audit. Filesystem and image vulnerability scanning use Trivy. Dockerfile linting uses Hadolint. IaC checks use Checkov for implemented infrastructure only.

Local environments may not have every specialist tool installed. The release evidence records local tool availability and CI workflow intent without claiming unavailable local scans passed. High or critical actionable findings are blocking unless a documented exception is added in a future milestone.
