from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.metadata import (
    build_sas_viya_metadata,
    comparable_metadata,
    reconcile_metadata,
)
from ml_product.lifecycle.package import build_model_package


def test_metadata_mapping_contains_required_custom_properties() -> None:
    package = build_model_package(LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")))

    metadata = build_sas_viya_metadata(package)
    custom = metadata["metadata"]["customProperties"]

    assert metadata["model"]["name"] == "long_stay_admission_risk"
    assert metadata["version"]["modelType"] == "xgboost"
    assert custom["feature_count"] == 71
    assert custom["dataset_version"] == "0.5.0"
    assert custom["registry_status"] == "registered"


def test_reconciliation_detects_matches_and_mismatches() -> None:
    package = build_model_package(LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")))
    external = comparable_metadata(package)

    matched = reconcile_metadata(package, {"customProperties": external})
    external["feature_count"] = 999
    mismatched = reconcile_metadata(package, {"customProperties": external})

    assert matched.status == "matched"
    assert mismatched.status == "mismatch"
    assert mismatched.mismatches["feature_count"]["external"] == 999
