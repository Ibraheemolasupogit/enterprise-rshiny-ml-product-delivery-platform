from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.package import build_model_package


def test_model_lifecycle_package_contract_contains_review_governance_boundary() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    package = build_model_package(config)
    payload = package.model_dump(mode="json")

    for key in (
        "model_name",
        "model_version",
        "model_family",
        "target",
        "source",
        "feature_metadata",
        "evaluation_metrics",
        "fairness_summary",
        "threshold_calibration_metadata",
        "artefacts",
        "governance_status",
        "created_at_utc",
    ):
        assert key in payload
    assert payload["governance_status"]["registration_allowed"] is True
    assert payload["governance_status"]["approval_granted"] is False
    assert payload["governance_status"]["activation_status"] == "inactive"
    assert payload["provider_contract"]["selected_provider"] == "local"
