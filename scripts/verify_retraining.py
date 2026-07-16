"""Verify deterministic Milestone 12 retraining evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ml_product.retraining import ComparisonConfig, RetrainingConfig, run_retraining

ROOT = Path(__file__).resolve().parents[1]


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = RetrainingConfig.from_file(ROOT / "config/retraining.yaml")
    comparison = ComparisonConfig.from_file(ROOT / "config/champion_challenger.yaml")
    registry_before = checksum(ROOT / "models/registry.json")
    first = run_retraining(config, comparison, root=ROOT, replace=True)
    first_summary = json.dumps(first, sort_keys=True)
    second = run_retraining(config, comparison, root=ROOT, replace=True)
    second_summary = json.dumps(second, sort_keys=True)
    if first_summary != second_summary:
        raise SystemExit("Retraining recommendation is not deterministic.")
    if checksum(ROOT / "models/registry.json") != registry_before:
        raise SystemExit("Retraining mutated the real registry.")
    recommendation = json.loads(
        (ROOT / "reports/retraining/retraining_recommendation.json").read_text(encoding="utf-8")
    )
    if recommendation["automatic_action"] != "none":
        raise SystemExit("Retraining recommendation contains automatic action.")
    if recommendation["approval_status"] != "not_granted":
        raise SystemExit("Retraining recommendation granted approval.")
    if recommendation["activation_status"] != "inactive":
        raise SystemExit("Retraining recommendation activated a model.")
    print("Retraining reproducibility verification passed.")


if __name__ == "__main__":
    main()
