from pathlib import Path

from ml_product.release.config import ReleaseConfig
from ml_product.release.readiness import assess_release_readiness


def test_release_readiness_allows_local_review_and_blocks_operational() -> None:
    config = ReleaseConfig.from_file(Path("config/release.yaml"))
    result = assess_release_readiness(config, Path("."))
    assert result["local_review_readiness"] == "ready_for_local_review"
    assert result["operational_release_readiness"] == "blocked_for_operational_release"
    assert result["operational_gates"]["approved_model_exists"] is False
    assert result["operational_gates"]["active_model_exists"] is False
    assert result["external_deployment_state"] == "not_performed"
