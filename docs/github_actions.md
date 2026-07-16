# GitHub Actions

The workflow set is split into quality, Python tests, R tests, integration tests, security, container, and release assurance. All workflows use `contents: read` permissions and safe triggers: pull request, push to `main`, and manual dispatch where applicable.

Actions are pinned to release tags with comments requiring commit SHA pinning after the first remote CI baseline. No workflow contains deployment commands, image publication, GitHub release creation, model approval, model activation, or retraining registration.
