# Dependency Assurance

Python dependency declarations are held in `pyproject.toml` with development support in `requirements-dev.txt`. R dependencies are locked through `renv.lock`. Milestone 13 adds committed dependency summaries under `reports/assurance`.

The summaries are inventory and policy evidence, not a guarantee that every future vulnerability is absent. Hosted CI runs dependency audit commands when the repository is pushed. Local evidence distinguishes configured scans from scans that were not available locally.
