"""Release manifest construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.release.config import ReleaseConfig
from ml_product.release.inventory import release_inventory
from ml_product.release.versioning import git_revision, project_version, release_tag


def build_release_manifest(config: ReleaseConfig, root: Path) -> dict[str, Any]:
    version = project_version(root)
    revision = git_revision(root)
    tag = release_tag(version, revision)
    remote_ci_reason = (
        "repository has no commits and has not been pushed"
        if revision == "uncommitted"
        else "remote CI is recorded separately in Milestone 14 remote CI evidence"
    )
    return {
        "milestone": 13,
        "project_version": version,
        "git_revision": revision,
        "image_revision": revision,
        "release_tag": tag,
        "api_image": f"{config.artefacts.api_image_name}:{tag}",
        "rshiny_image": f"{config.artefacts.rshiny_image_name}:{tag}",
        "publish_images": config.artefacts.publish_images,
        "cloud_deployment_enabled": config.deployment.cloud_enabled,
        "external_deployment_enabled": config.deployment.external_enabled,
        "manual_approval_required": config.deployment.require_manual_approval,
        "operational_release_requires_approved_active_model": (
            config.model.require_approved_active_for_operational_release
        ),
        "local_review_label": config.model.review_release_label,
        "inventory": release_inventory(root),
        "remote_ci_executed": False,
        "remote_ci_reason": remote_ci_reason,
    }
