"""Release validation entry points."""

from __future__ import annotations

from pathlib import Path

from ml_product.release.config import ReleaseConfig
from ml_product.release.containers import validate_container_files


def validate_release_config(config: ReleaseConfig) -> dict[str, object]:
    return {
        "valid": True,
        "publish_images": config.artefacts.publish_images,
        "cloud_enabled": config.deployment.cloud_enabled,
        "external_enabled": config.deployment.external_enabled,
        "manual_approval_required": config.deployment.require_manual_approval,
        "review_release_label": config.model.review_release_label,
    }


def validate_containers(root: Path) -> dict[str, object]:
    return validate_container_files(root)
