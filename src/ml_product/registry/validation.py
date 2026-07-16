"""Validate registry and generated Milestone 7 evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.registry.config import RegistryConfig
from ml_product.registry.storage import load_registry, read_json

REQUIRED_REGISTRY_EVIDENCE = [
    "model_registry_manifest.json",
    "registry_validation.json",
    "governance_review.json",
    "approval_decision.json",
    "activation_status.json",
    "serving_contract.json",
    "serving_readiness.json",
    "registry_audit_summary.json",
    "model_serving_report.md",
]


def validate_registry(config: RegistryConfig, *, root: Path = Path(".")) -> dict[str, Any]:
    errors: list[str] = []
    registry_path = root / config.registry.metadata_path
    record = load_registry(registry_path)
    if config.approval.automatic_approval:
        errors.append("Automatic approval must be disabled.")
    if not config.activation.require_approved_status:
        errors.append("Activation must require approval.")
    for entry in record.models:
        for version in entry.versions:
            if version.status == "active" and version.approval_decision is None:
                errors.append("Active model lacks approval decision.")
            if version.status in {"registered", "approval_pending"} and version.activation_event:
                errors.append("Unapproved model must not have activation event.")
            if "/Users/" in version.model_dump_json():
                errors.append("Registry metadata contains user-specific absolute path.")
    report_dir = root / "reports/model_evaluation"
    for file_name in REQUIRED_REGISTRY_EVIDENCE:
        path = report_dir / file_name
        if not path.is_file():
            errors.append(f"Missing registry evidence: {file_name}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "/Users/" in text:
            errors.append(f"Registry evidence contains user-specific absolute path: {file_name}")
    readiness_path = report_dir / "serving_readiness.json"
    if readiness_path.is_file():
        readiness = read_json(readiness_path)
        if readiness.get("production_deployment") is not False:
            errors.append("Serving readiness must not claim production deployment.")
    return {"valid": not errors, "errors": errors}
