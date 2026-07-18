from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.package import build_model_package, write_model_package


def test_model_package_is_deterministic_and_contains_required_metadata() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))

    first = build_model_package(config)
    second = build_model_package(config)

    assert first == second
    assert first.model_name == "long_stay_admission_risk"
    assert first.model_version == 1
    assert first.model_family == "xgboost"
    assert first.source["eligible_row_count"] == 117
    assert first.feature_metadata["feature_count"] == 71
    assert first.evaluation_metrics["locked_test"]["pr_auc"] > 0
    assert first.governance_status["approval_granted"] is False
    assert first.governance_status["activation_status"] == "inactive"


def test_model_package_write_does_not_mutate_registry(tmp_path: Path) -> None:
    registry_path = Path("models/registry.json")
    before = registry_path.read_text(encoding="utf-8")
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    package = build_model_package(config)

    destination = write_model_package(package, tmp_path / "package.json")

    assert destination.is_file()
    assert registry_path.read_text(encoding="utf-8") == before
