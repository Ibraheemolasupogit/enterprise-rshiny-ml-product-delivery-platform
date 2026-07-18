from pathlib import Path
from typing import Any

from ml_product.lifecycle.config import LifecycleConfig, RegistrationConfig
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.models import LinkageRecord, PromotionRequest
from ml_product.lifecycle.package import build_model_package
from ml_product.lifecycle.promotion import (
    approval_reference,
    build_champion_challenger_comparison,
    promotion_decision,
    write_promotion_evidence,
)
from ml_product.lifecycle.sas_viya_client import HttpResponse
from ml_product.lifecycle.sas_viya_provider import SasViyaLifecycleProvider


class PromotionTransport:
    def __init__(self, *, already_champion: bool = False) -> None:
        self.already_champion = already_champion
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        timeout: int,
        verify: bool,
        json_body: dict[str, Any] | None = None,
    ) -> HttpResponse:
        del headers, timeout, verify, json_body
        self.calls.append({"method": method, "url": url})
        if "/repositories?name=" in url:
            return _response({"items": [{"id": "repo-1"}]})
        if url.endswith("/champion") and method == "GET":
            if not self.already_champion:
                return _response({"items": []})
            return _response(
                {
                    "id": "model-1",
                    "modelId": "model-1",
                    "versionId": "version-1",
                    "modelName": "long_stay_admission_risk",
                    "localModelVersion": 1,
                    "registrationFingerprint": _fingerprint(),
                }
            )
        if url.endswith("/promote"):
            return _response({"id": "promotion-1"})
        if url.endswith("/champion") and method == "PUT":
            return _response({"id": "champion-1"})
        return _response({})


def test_comparison_blocks_without_external_registration() -> None:
    package = _package()

    comparison = build_champion_challenger_comparison(
        package,
        provider="sas_viya",
        champion=None,
        linkage=None,
    )

    assert comparison.promotion_eligibility == "blocked"
    assert "external lifecycle provider" in comparison.blocking_reasons[0]


def test_comparison_blocks_without_approval() -> None:
    package = _package()
    linkage = _linkage()

    decision = promotion_decision(
        build_champion_challenger_comparison(
            package,
            provider="sas_viya",
            champion=None,
            linkage=linkage,
        )
    )

    assert decision.status == "blocked"
    assert approval_reference(package).approval_status == "missing"


def test_promotion_evidence_has_checksum_and_no_credentials(tmp_path: Path) -> None:
    package = _package()
    result = SasViyaLifecycleProvider(
        _sas_config().sas_viya,
        registration_config=RegistrationConfig(
            linkage_path=tmp_path / "linkage.json",
            evidence_directory=tmp_path / "registration",
            promotion_evidence_directory=tmp_path / "promotion",
        ),
        transport=PromotionTransport(),
    ).promote_approved_model_version(
        PromotionRequest(
            provider="sas_viya",
            model_name=package.model_name,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id="model-1",
            external_model_version_id="version-1",
            registration_fingerprint=registration_fingerprint(package),
            requested_by="test",
            reason="test",
        ),
        confirm_external=True,
    )
    result = write_promotion_evidence(result, evidence_directory=tmp_path / "promotion")

    assert result.evidence_checksum is not None
    evidence = next((tmp_path / "promotion").glob("*.json")).read_text(encoding="utf-8")
    assert "Authorization" not in evidence
    assert "SAS_VIYA_ACCESS_TOKEN" not in evidence


def test_repeated_promotion_returns_already_champion_without_post() -> None:
    package = _package()
    transport = PromotionTransport(already_champion=True)
    provider = SasViyaLifecycleProvider(
        _sas_config().sas_viya,
        registration_config=RegistrationConfig(),
        transport=transport,
    )

    result = provider.promote_approved_model_version(
        PromotionRequest(
            provider="sas_viya",
            model_name=package.model_name,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id="model-1",
            external_model_version_id="version-1",
            registration_fingerprint=registration_fingerprint(package),
            requested_by="test",
            reason="test",
        ),
        confirm_external=True,
    )

    assert result.promotion_status == "already_champion"
    assert not any(call["method"] == "POST" for call in transport.calls)


def _package() -> Any:
    return build_model_package(LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")))


def _sas_config() -> LifecycleConfig:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    payload = config.model_dump()
    payload["provider"]["selected"] = "sas_viya"
    payload["sas_viya"]["enabled"] = True
    payload["sas_viya"]["authentication_mode"] = "none"
    return LifecycleConfig.model_validate(payload)


def _linkage() -> LinkageRecord:
    package = _package()
    return LinkageRecord(
        provider="sas_viya",
        local_model_id=package.registry_id,
        local_model_version=package.model_version,
        local_build_identifier=package.candidate_identifier,
        registration_fingerprint=registration_fingerprint(package),
        external_project_id="repo-1",
        external_model_id="model-1",
        external_model_version_id="version-1",
        metadata_sync_status="synchronised",
        first_registered_at_utc="2026-07-18T00:00:00+00:00",
        last_reconciled_at_utc="2026-07-18T00:00:00+00:00",
    )


def _fingerprint() -> str:
    return registration_fingerprint(_package())


def _response(payload: dict[str, Any]) -> HttpResponse:
    import json

    return HttpResponse(200, json.dumps(payload), {})
