# Container Architecture

Milestone 13 separates the FastAPI scoring service from the R-Shiny product UI. The API image contains the Python runtime, registry metadata, and mounted or locally staged model artefacts. The R-Shiny image contains only the UI, R dependencies, and committed evidence required for read-only display.

Both images run as non-root users, expose only local service ports, include health checks, and use OCI labels. Model binaries remain uncommitted and are generated or mounted for local validation. The base Compose mode keeps review mode disabled; `docker-compose.review.yml` explicitly labels local review as unapproved and non-operational.
