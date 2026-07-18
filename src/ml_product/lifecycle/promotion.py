"""Champion-challenger and promotion helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.linkage import LinkageStore, sha256_json
from ml_product.lifecycle.models import (
    ApprovalEvidenceReference,
    ChallengerReference,
    ChampionChallengerComparison,
    ChampionReference,
    ExternalLifecycleReconciliation,
    LinkageRecord,
    PromotionDecision,
    PromotionResult,
    PromotionStatus,
)
from ml_product.lifecycle.package import ModelLifecyclePackage
from ml_product.utils.paths import repository_root


def approval_reference(package: ModelLifecyclePackage) -> ApprovalEvidenceReference:
    decision = package.governance_status.get("approval_decision")
    if not isinstance(decision, dict):
        return ApprovalEvidenceReference(approval_status="missing")
    value = decision.get("decision")
    if value in {"approve", "approve_with_conditions"}:
        approval_status: LiteralApprovalStatus = "approved"
    elif value == "reject":
        approval_status = "rejected"
    else:
        approval_status = "pending"
    return ApprovalEvidenceReference(
        approval_status=approval_status,
        actor=_string_or_none(decision.get("actor")),
        decided_at_utc=_string_or_none(decision.get("decided_at_utc")),
        evidence_fingerprint=_string_or_none(decision.get("evidence_fingerprint")),
        reason=_string_or_none(decision.get("reason")),
    )


def challenger_from_package(
    package: ModelLifecyclePackage,
    *,
    provider: str,
    linkage: LinkageRecord | None = None,
) -> ChallengerReference:
    return ChallengerReference(
        provider=provider,
        model_name=package.model_name,
        local_model_id=package.registry_id,
        local_model_version=package.model_version,
        local_build_identifier=package.candidate_identifier,
        external_model_id=None if linkage is None else linkage.external_model_id,
        external_model_version_id=None if linkage is None else linkage.external_model_version_id,
        registration_fingerprint=registration_fingerprint(package),
        lifecycle_state=str(package.governance_status.get("registry_status", "registered")),
    )


def build_champion_challenger_comparison(
    package: ModelLifecyclePackage,
    *,
    provider: str,
    champion: ChampionReference | None,
    linkage: LinkageRecord | None,
) -> ChampionChallengerComparison:
    challenger = challenger_from_package(package, provider=provider, linkage=linkage)
    approval = approval_reference(package)
    blocking = promotion_blocking_reasons(
        package,
        champion=champion,
        linkage=linkage,
        approval=approval,
    )
    eligibility: PromotionStatus = "eligible" if not blocking else "blocked"
    if (
        champion is not None
        and champion.registration_fingerprint == challenger.registration_fingerprint
    ):
        eligibility = "already_champion"
        blocking = []
    return ChampionChallengerComparison(
        provider=provider,
        champion=champion,
        challenger=challenger,
        model_family=package.model_family,
        dataset_version=_string_or_none(package.source.get("dataset_version")),
        source_fingerprint=_string_or_none(package.source.get("source_fingerprint")),
        key_evaluation_metrics=package.evaluation_metrics.get("registry_summary", {}),
        threshold_summary={
            "selected_threshold": package.threshold_calibration_metadata.get(
                "selected_threshold"
            ),
            "selection_rule": package.threshold_calibration_metadata.get("selection_rule"),
        },
        calibration_summary={
            "selected_calibration": package.threshold_calibration_metadata.get(
                "selected_calibration"
            ),
            "reason": package.threshold_calibration_metadata.get(
                "calibration_selection_reason"
            ),
        },
        fairness_summary=package.fairness_summary,
        governance_status=package.governance_status,
        approval=approval,
        compatibility_status="compatible",
        promotion_eligibility=eligibility,
        blocking_reasons=blocking,
    )


def promotion_blocking_reasons(
    package: ModelLifecyclePackage,
    *,
    champion: ChampionReference | None,
    linkage: LinkageRecord | None,
    approval: ApprovalEvidenceReference,
) -> list[str]:
    del champion
    reasons: list[str] = []
    if linkage is None:
        reasons.append("Candidate is not registered with the external lifecycle provider.")
    elif linkage.metadata_sync_status == "mismatch":
        reasons.append("External lifecycle metadata has material reconciliation mismatches.")
    if approval.approval_status != "approved":
        reasons.append("Governance approval is missing or not approved.")
    if not package.evaluation_metrics.get("registry_summary"):
        reasons.append("Required evaluation evidence is absent.")
    hard_requirements = package.governance_status.get("hard_requirements", {})
    if isinstance(hard_requirements, dict):
        failed = sorted(key for key, value in hard_requirements.items() if value is False)
        reasons.extend(f"Governance hard requirement failed: {key}." for key in failed)
    return reasons


def promotion_decision(comparison: ChampionChallengerComparison) -> PromotionDecision:
    return PromotionDecision(
        status=comparison.promotion_eligibility,
        eligible=comparison.promotion_eligibility in {"eligible", "already_champion"},
        blocking_reasons=comparison.blocking_reasons,
        approval=comparison.approval,
    )


def reconcile_external_lifecycle(
    *,
    local_active_version: int | None,
    external_champion: ChampionReference | None,
) -> ExternalLifecycleReconciliation:
    if external_champion is None:
        return ExternalLifecycleReconciliation(
            status="missing_external",
            local_active_version=local_active_version,
            external_champion_version_id=None,
        )
    external_version = external_champion.local_model_version
    status: LiteralLifecycleReconciliationStatus = (
        "aligned" if local_active_version == external_version else "divergent"
    )
    return ExternalLifecycleReconciliation(
        status=status,
        local_active_version=local_active_version,
        external_champion_version_id=external_champion.external_model_version_id,
        details={"external_local_version": external_version},
    )


def write_promotion_evidence(
    result: PromotionResult,
    *,
    evidence_directory: Path,
) -> PromotionResult:
    directory = (
        evidence_directory
        if evidence_directory.is_absolute()
        else repository_root() / evidence_directory
    )
    directory.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": "lifecycle-promotion-evidence/v1",
        "provider": result.provider,
        "local_identity": {
            "local_model_id": result.local_model_id,
            "local_model_version": result.local_model_version,
        },
        "external_identity": {
            "external_model_id": result.external_model_id,
            "external_model_version_id": result.external_model_version_id,
        },
        "registration_fingerprint": result.registration_fingerprint,
        "champion_before": None
        if result.champion_before is None
        else result.champion_before.model_dump(mode="json"),
        "champion_after": None
        if result.champion_after is None
        else result.champion_after.model_dump(mode="json"),
        "approval_evidence": result.approval.model_dump(mode="json"),
        "eligibility_checks": result.blocking_reasons,
        "decision": result.promotion_status,
        "local_activation_performed": result.local_activation_performed,
        "reconciliation_result": None
        if result.reconciliation is None
        else result.reconciliation.model_dump(mode="json"),
        "written_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    checksum = sha256_json(payload)
    payload["evidence_checksum"] = checksum
    path = directory / f"{result.registration_fingerprint}-promotion.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        display_path = path.relative_to(repository_root())
    except ValueError:
        display_path = path
    return result.model_copy(
        update={"evidence_path": str(display_path), "evidence_checksum": checksum}
    )


def linkage_for_package(
    package: ModelLifecyclePackage,
    *,
    provider: str,
    linkage_path: Path,
) -> LinkageRecord | None:
    return LinkageStore(linkage_path).find(provider, registration_fingerprint(package))


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


LiteralApprovalStatus = Literal["missing", "pending", "approved", "rejected"]
LiteralLifecycleReconciliationStatus = Literal[
    "aligned", "divergent", "missing_external", "reconciliation_required"
]
