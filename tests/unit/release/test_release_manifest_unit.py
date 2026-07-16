import re
from pathlib import Path

from ml_product.release.config import ReleaseConfig
from ml_product.release.manifest import build_release_manifest


def is_revision_or_uncommitted(value: str) -> bool:
    return value == "uncommitted" or re.fullmatch(r"[0-9a-f]{40}", value) is not None


def test_release_manifest_does_not_invent_remote_ci() -> None:
    manifest = build_release_manifest(
        ReleaseConfig.from_file(Path("config/release.yaml")), Path(".")
    )
    assert manifest["remote_ci_executed"] is False
    assert is_revision_or_uncommitted(manifest["git_revision"])
    assert manifest["image_revision"] == manifest["git_revision"]
    assert manifest["publish_images"] is False
    assert manifest["external_deployment_enabled"] is False
