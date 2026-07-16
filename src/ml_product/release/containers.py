"""Container metadata validation for Milestone 13."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml


def _dockerfile_text(root: Path, name: str) -> str:
    return (root / "infrastructure" / "docker" / name).read_text(encoding="utf-8")


def validate_container_files(root: Path) -> dict[str, Any]:
    api = _dockerfile_text(root, "Dockerfile.api")
    rshiny = _dockerfile_text(root, "Dockerfile.rshiny")
    compose = yaml.safe_load((root / "docker-compose.yml").read_text(encoding="utf-8"))
    review = yaml.safe_load((root / "docker-compose.review.yml").read_text(encoding="utf-8"))
    checks = {
        "api_non_root_user": "USER appuser" in api,
        "rshiny_non_root_user": "USER shiny" in rshiny,
        "api_healthcheck": "HEALTHCHECK" in api,
        "rshiny_healthcheck": "HEALTHCHECK" in rshiny,
        "api_base_pinned": "python:3.12.8-slim-bookworm" in api,
        "rshiny_base_pinned": "r-base:4.4.2" in rshiny,
        "review_mode_disabled_by_default": "SERVING_REVIEW_MODE" not in str(compose),
        "review_override_labelled": "local review only" in str(review).lower(),
        "no_privileged_mode": "privileged" not in str(compose).lower(),
        "no_docker_socket": "/var/run/docker.sock" not in str(compose),
    }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "compose_services": sorted((compose.get("services") or {}).keys()),
        "review_services": sorted((review.get("services") or {}).keys()),
        "api_dockerfile_sha256": hashlib.sha256(api.encode("utf-8")).hexdigest(),
        "rshiny_dockerfile_sha256": hashlib.sha256(rshiny.encode("utf-8")).hexdigest(),
    }
