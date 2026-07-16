# CI/CD Architecture

Milestone 13 implements a controlled delivery pipeline for a synthetic R-Shiny and FastAPI ML product. The flow is developer change, static validation, Python and R tests, contract and integration tests, browser-backed Shiny tests, security checks, deterministic evidence verification, container builds, container validation, bounded local deployment smoke tests, release evidence generation, and a manual approval boundary.

The workflows are intentionally non-deploying. They do not approve models, activate models, publish images, provision cloud resources, create releases, create tags, or trigger retraining from push events. Remote GitHub Actions will only become genuine after the repository receives its first commit and is pushed.
