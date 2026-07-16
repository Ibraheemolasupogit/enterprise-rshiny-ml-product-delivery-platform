"""Release readiness gate evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.release.config import ReleaseConfig
from ml_product.release.containers import validate_container_files
from ml_product.release.governance import model_governance_state
from ml_product.release.security import security_summary


def assess_release_readiness(config: ReleaseConfig, root: Path) -> dict[str, Any]:
    governance = model_governance_state(root)
    security = security_summary(root)
    containers = validate_container_files(root)
    hard_gates = {
        "release_config_valid": True,
        "registry_valid": governance["registry_version"] == 1,
        "monitoring_boundary_valid": True,
        "retraining_boundary_valid": governance["retraining_automatic_action"] == "none",
        "security_scans_within_policy": security["overall_status"] == "passed",
        "container_files_valid": containers["status"] == "passed",
        "external_deployment_disabled": not config.deployment.external_enabled,
        "image_publication_disabled": not config.artefacts.publish_images,
        "manual_approval_required": config.deployment.require_manual_approval,
    }
    operational_gates = {
        "approved_model_exists": governance["approval_status"] == "approved",
        "active_model_exists": governance["latest_model_status"] == "active",
        "approved_active_model_exists": governance["approved_active_model_exists"],
        "deployment_target_configured": config.deployment.external_enabled,
        "deployment_approval_granted": False,
    }
    local_ready = all(hard_gates.values()) and config.model.permit_review_release
    operational_ready = all(hard_gates.values()) and all(operational_gates.values())
    return {
        "local_review_readiness": "ready_for_local_review" if local_ready else "invalid",
        "operational_release_readiness": (
            "ready_for_operational_release"
            if operational_ready
            else "blocked_for_operational_release"
        ),
        "hard_gates": hard_gates,
        "operational_gates": operational_gates,
        "blocking_gates": [name for name, passed in operational_gates.items() if not passed],
        "manual_approval_required": config.deployment.require_manual_approval,
        "model_approval_state": governance["approval_status"],
        "model_activation_state": governance["activation_status"],
        "external_deployment_state": "not_performed",
        "governance": governance,
        "security": security,
        "containers": containers,
    }
