import json
from pathlib import Path

from ml_product.monitoring import (
    DriftThresholdConfig,
    MonitoringConfig,
    run_monitoring,
)


def _load(output_dir: Path, name: str) -> dict:
    return json.loads((output_dir / name).read_text(encoding="utf-8"))


def test_monitoring_run_is_review_only(tmp_path: Path) -> None:
    config = MonitoringConfig.from_file(Path("config/monitoring.yaml"))
    thresholds = DriftThresholdConfig.from_file(Path("config/drift_thresholds.yaml"))

    result = run_monitoring(
        config,
        thresholds,
        current_window=Path("tests/fixtures/monitoring/moderate_drift"),
        output_dir=tmp_path,
        replace=True,
    )

    review = _load(tmp_path, "monitoring_review.json")
    prediction = _load(tmp_path, "prediction_drift.json")
    performance = _load(tmp_path, "performance_monitoring.json")
    assert result["overall_disposition"] == "review_required"
    assert result["automatic_action"] == "none"
    assert review["registry_mutation_status"] == "none"
    assert review["model_replacement_status"] == "none"
    assert prediction["performance_conclusion_available"] is False
    assert performance["labels_available"] is True
    assert (tmp_path / "monitoring_summary.json").is_file()


def test_unlabelled_prediction_drift_does_not_claim_performance(tmp_path: Path) -> None:
    config = MonitoringConfig.from_file(Path("config/monitoring.yaml"))
    thresholds = DriftThresholdConfig.from_file(Path("config/drift_thresholds.yaml"))

    run_monitoring(
        config,
        thresholds,
        current_window=Path("tests/fixtures/monitoring/prediction_drift"),
        output_dir=tmp_path,
        replace=True,
    )

    prediction = _load(tmp_path, "prediction_drift.json")
    performance = _load(tmp_path, "performance_monitoring.json")
    review = _load(tmp_path, "monitoring_review.json")
    assert prediction["status"] in {"warning", "critical"}
    assert performance["status"] == "insufficient_evidence"
    assert performance["labels_available"] is False
    assert review["retraining_status"] == "not_implemented"
