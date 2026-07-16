from pathlib import Path

import pytest

from ml_product.release.config import ReleaseConfig


def test_release_config_blocks_publication_and_cloud() -> None:
    config = ReleaseConfig.from_file(Path("config/release.yaml"))
    assert config.artefacts.publish_images is False
    assert config.deployment.cloud_enabled is False
    assert config.deployment.external_enabled is False
    assert config.deployment.require_manual_approval is True


def test_release_config_rejects_publish_images() -> None:
    config = ReleaseConfig.from_file(Path("config/release.yaml"))
    payload = config.model_dump()
    payload["artefacts"]["publish_images"] = True
    with pytest.raises(ValueError, match="publish"):
        ReleaseConfig.model_validate(payload)


def test_release_config_rejects_unsafe_image_name() -> None:
    config = ReleaseConfig.from_file(Path("config/release.yaml"))
    payload = config.model_dump()
    payload["artefacts"]["api_image_name"] = "registry.example.com/api:latest"
    with pytest.raises(ValueError, match="Image names"):
        ReleaseConfig.model_validate(payload)
