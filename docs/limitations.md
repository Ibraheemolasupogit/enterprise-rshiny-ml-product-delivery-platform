# Limitations

This repository currently contains foundations, deterministic synthetic source-system samples, a local governed DuckDB logical layer, deterministic Milestone 5 feature engineering, Milestone 6 candidate model-development evidence, Milestone 7 local registry and serving controls, advanced R-Shiny workflows, Milestone 11 synthetic monitoring evidence, and Milestone 12 controlled retraining review.

- Synthetic data only.
- No clinical use.
- No automated care decisions.
- No real NHS integration.
- No HMRC integration.
- Local DuckDB database and governed logical views exist, but no real external database service exists.
- Candidate model development, local registration, review-mode serving and synthetic monitoring exist for the admission-time contract only; no model is approved, active, retrained, externally served, or deployed.
- Local macOS XGBoost development requires a compatible OpenMP runtime such as Homebrew `libomp`; this is an environment prerequisite, not a product runtime dependency.
- Real Denodo integration is externally blocked because genuine access is unavailable.
- No completed SAS Viya integration.
- No deployed staging or production environment.
- Local FastAPI service exists, but it fails closed by default because no approved active model exists.
- No registry administration, automatic model replacement, deployment, approval, activation or rollback behaviour.
- Monitoring outputs are synthetic and review-only; they do not mutate model lifecycle state.

Milestone 1 is complete. Milestone 2 is complete. Milestone 3 is complete. Milestone 4 is externally blocked. Milestone 5 is complete. Milestone 6 is complete. Milestone 7 is complete. Milestone 8 is externally blocked. Milestone 9 is complete. Milestone 10 is complete. Milestone 11 is complete. Milestone 12 is complete. Milestones 13–14 remain planned.
## Milestone 10 Limitations

Advanced R-Shiny outputs remain synthetic and local. The model is registered for review only, approval is pending, activation is inactive, and governance recommends defer. Locked test specificity is 0.4 and balanced accuracy is approximately 0.561.

Milestone 11 adds monitoring and drift detection after Milestone 10. There is still no retraining, production deployment, clinical validation, Denodo integration, or SAS Viya integration.
## Milestone 13

Remote CI has not run because the repository has no commits and has not been pushed. Local security summaries record missing specialist tools honestly. Container validation is local and bounded. No image registry, cloud deployment, GitHub release, approved active model, or operational serving path exists in this milestone.
