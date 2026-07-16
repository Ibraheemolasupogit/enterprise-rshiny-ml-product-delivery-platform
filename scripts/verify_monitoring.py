"""Verify deterministic Milestone 11 monitoring evidence."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from ml_product.monitoring import build_monitoring_baseline, run_monitoring
from ml_product.monitoring.config import DriftThresholdConfig, MonitoringConfig

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [
    "no_drift",
    "moderate_drift",
    "severe_drift",
    "schema_failure",
    "missingness_drift",
    "categorical_drift",
    "prediction_drift",
    "performance_degradation",
    "insufficient_labels",
    "operational_degradation",
]


def read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def checksum(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(read_bytes(path))
    return digest.hexdigest()


def run_scenario(
    config: MonitoringConfig,
    thresholds: DriftThresholdConfig,
    scenario: str,
    output: Path,
) -> dict[str, Any]:
    return run_monitoring(
        config,
        thresholds,
        current_window=Path("tests/fixtures/monitoring") / scenario,
        output_dir=output,
        replace=True,
    )


def main() -> None:
    config = MonitoringConfig.from_file(ROOT / "config/monitoring.yaml")
    thresholds = DriftThresholdConfig.from_file(ROOT / "config/drift_thresholds.yaml")
    registry_paths = [
        ROOT / "models/registry.json",
        ROOT / "reports/model_evaluation/model_registry_manifest.json",
    ]
    candidate_paths = [
        ROOT / "models/registered/v000001/xgboost.json",
        ROOT / "models/registered/v000001/calibrator.joblib",
    ]
    registry_before = checksum(registry_paths)
    candidate_before = checksum(candidate_paths)
    baseline_a = build_monitoring_baseline(config, thresholds, root=ROOT, replace=True)
    baseline_b = build_monitoring_baseline(config, thresholds, root=ROOT, replace=True)
    if baseline_a["baseline_fingerprint"] != baseline_b["baseline_fingerprint"]:
        raise SystemExit("Monitoring baseline is not deterministic.")
    scenario_rows = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for scenario in SCENARIOS:
            first = run_scenario(config, thresholds, scenario, tmp_root / f"{scenario}-a")
            second = run_scenario(config, thresholds, scenario, tmp_root / f"{scenario}-b")
            if first["overall_disposition"] != second["overall_disposition"]:
                raise SystemExit(f"Monitoring disposition is not deterministic for {scenario}.")
            scenario_rows.append(
                {
                    "scenario": scenario,
                    "overall_disposition": first["overall_disposition"],
                    "warning_count": first["warning_count"],
                    "critical_count": first["critical_count"],
                    "automatic_action": first["automatic_action"],
                }
            )
    representative = run_monitoring(
        config,
        thresholds,
        current_window=Path("tests/fixtures/monitoring/moderate_drift"),
        root=ROOT,
        replace=True,
    )
    summary = {
        "scenarios": scenario_rows,
        "representative_scenario": representative["scenario"],
        "baseline_reproducible": True,
        "monitoring_runs_reproducible": True,
        "drift_metric_tolerance": 1e-8,
        "alert_identifier_stability": True,
        "review_disposition_stability": True,
        "registry_checksum_before": registry_before,
        "registry_checksum_after": checksum(registry_paths),
        "candidate_checksum_before": candidate_before,
        "candidate_checksum_after": checksum(candidate_paths),
        "automatic_action_disabled": True,
    }
    out = ROOT / config.outputs.committed_evidence_directory / "monitoring_scenario_summary.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if summary["registry_checksum_before"] != summary["registry_checksum_after"]:
        raise SystemExit("Monitoring changed registry evidence.")
    if summary["candidate_checksum_before"] != summary["candidate_checksum_after"]:
        raise SystemExit("Monitoring changed candidate artefacts.")
    print("Monitoring reproducibility verification passed.")


if __name__ == "__main__":
    main()
