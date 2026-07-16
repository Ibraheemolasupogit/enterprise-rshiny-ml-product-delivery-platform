# Portfolio Screenshot Runbook

Capture screenshots only after the repository is committed, pushed and CI is genuinely green. Use `reports/portfolio/screenshots/YYYYMMDD-<subject>.png` naming. Redact tokens, local usernames, browser profile details and any secrets.

- GitHub repository overview: show README and repository description.
- GitHub Actions green workflows: show real workflow names and green conclusions.
- Architecture diagram: show Mermaid-rendered architecture.
- R-Shiny Overview, Single Prediction, Cohort Scoring, Model Performance, Monitoring, Retraining Review and Model Governance: run the local review stack and show the visible review-mode status.
- API OpenAPI page: show `/docs` with no credentials.
- Local Compose services: show bounded localhost services only.
- Release-assurance output, Security/SBOM evidence: show committed evidence files.

Do not capture fabricated Denodo or SAS Viya screenshots.
