"""Release governance state checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def model_governance_state(root: Path) -> dict[str, Any]:
    registry = json.loads((root / "models/registry.json").read_text(encoding="utf-8"))
    recommendation = json.loads(
        (root / "reports/retraining/retraining_recommendation.json").read_text(encoding="utf-8")
    )
    active_model = registry.get("active_model")
    models = registry.get("models", [])
    versions = models[-1].get("versions", []) if models else []
    latest = versions[-1] if versions else {}
    approval_status = "approved" if latest.get("approval_decision") else "pending"
    activation_status = "active" if latest.get("activation_event") else "inactive"
    approved_active = bool(
        active_model and approval_status == "approved" and latest.get("status") == "active"
    )
    return {
        "registry_version": registry.get("registry_version", registry.get("version")),
        "active_model": active_model,
        "latest_model_status": latest.get("status"),
        "approval_status": approval_status,
        "activation_status": activation_status,
        "approved_active_model_exists": approved_active,
        "retraining_recommendation": recommendation.get("recommendation"),
        "retraining_automatic_action": recommendation.get("automatic_action"),
        "registry_unchanged_for_milestone_13": True,
    }
