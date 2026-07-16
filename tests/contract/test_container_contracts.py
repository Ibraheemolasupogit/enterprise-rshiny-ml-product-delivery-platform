from pathlib import Path

import yaml


def test_compose_default_and_review_modes_are_governed() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    review = yaml.safe_load(Path("docker-compose.review.yml").read_text(encoding="utf-8"))
    assert set(compose["services"]) == {"api", "rshiny"}
    assert "SERVING_REVIEW_MODE" not in str(compose)
    assert review["services"]["api"]["environment"]["SERVING_REVIEW_MODE"] == "true"
    assert "local review only" in str(review).lower()
    assert "/var/run/docker.sock" not in str(compose)
    assert "privileged" not in str(compose).lower()


def test_dockerfiles_have_non_root_users_and_healthchecks() -> None:
    api = Path("infrastructure/docker/Dockerfile.api").read_text(encoding="utf-8")
    rshiny = Path("infrastructure/docker/Dockerfile.rshiny").read_text(encoding="utf-8")
    assert "USER appuser" in api
    assert "USER shiny" in rshiny
    assert "HEALTHCHECK" in api
    assert "HEALTHCHECK" in rshiny
    assert "org.opencontainers.image.revision" in api
    assert "org.opencontainers.image.revision" in rshiny
