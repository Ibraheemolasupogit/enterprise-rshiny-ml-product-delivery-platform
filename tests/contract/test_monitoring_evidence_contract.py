import json
from pathlib import Path

MONITORING_FILES = [
    "monitoring_baseline_manifest.json",
    "monitoring_run_manifest.json",
    "schema_monitoring.json",
    "data_quality_monitoring.json",
    "numeric_drift.json",
    "categorical_drift.json",
    "missingness_drift.json",
    "prediction_drift.json",
    "performance_monitoring.json",
    "calibration_monitoring.json",
    "operational_monitoring.json",
    "monitoring_alerts.json",
    "monitoring_review.json",
    "monitoring_summary.json",
    "monitoring_scenario_summary.json",
]


def _load(name: str) -> dict:
    return json.loads((Path("reports/monitoring") / name).read_text(encoding="utf-8"))


def test_monitoring_evidence_files_exist_and_share_candidate() -> None:
    candidates = set()
    for name in MONITORING_FILES:
        path = Path("reports/monitoring") / name
        assert path.is_file(), name
        payload = _load(name)
        if "candidate_identifier" in payload:
            candidates.add(payload["candidate_identifier"])
        assert "/Users/" not in path.read_text(encoding="utf-8")
    assert candidates == {"CAND-85EA9202CAD6FE7F"}


def test_monitoring_alerts_are_review_only() -> None:
    alerts = _load("monitoring_alerts.json")["alerts"]
    assert alerts
    assert {alert["automatic_action"] for alert in alerts} <= {"human_review_required"}
    review = _load("monitoring_review.json")
    summary = _load("monitoring_summary.json")
    assert summary["automatic_action"] == "none"
    assert review["retraining_status"] == "not_implemented"
    assert review["registry_mutation_status"] == "none"
    assert review["model_replacement_status"] == "none"


def test_prediction_and_performance_contracts_are_separate() -> None:
    prediction = _load("prediction_drift.json")
    performance = _load("performance_monitoring.json")
    assert prediction["performance_conclusion_available"] is False
    assert "not performance drift" in prediction["boundary_statement"]
    assert performance["labels_available"] is True
    assert performance["threshold_unchanged"] is True
    assert performance["calibration_unchanged"] is True
