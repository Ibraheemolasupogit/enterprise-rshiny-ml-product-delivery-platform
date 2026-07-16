# Local Container Deployment

The local deployment has two bounded modes. Default governed mode starts API and R-Shiny, allows API liveness, reports readiness false because no approved active model exists, rejects predictions, and shows scoring unavailable in R-Shiny.

Explicit review mode uses `docker-compose.review.yml` with `SERVING_REVIEW_MODE=true`. It can load the registered unapproved model for local review only, and every prediction remains labelled unapproved and not for operational use. The smoke script stops containers and removes volumes through cleanup traps.
