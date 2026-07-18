from pathlib import Path
from typing import Any

from ml_product.lifecycle.config import LifecycleConfig, RegistrationConfig
from ml_product.lifecycle.metadata import comparable_metadata
from ml_product.lifecycle.package import build_model_package
from ml_product.lifecycle.sas_viya_client import HttpResponse
from ml_product.lifecycle.sas_viya_provider import SasViyaLifecycleProvider


class RegistrationTransport:
    def __init__(self) -> None:
        self.models: list[dict[str, Any]] = []
        self.versions: list[dict[str, Any]] = []
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
        del headers, timeout, verify
        self.calls.append({"method": method, "url": url, "json_body": json_body})
        if method == "GET" and "/repositories?name=" in url:
            return _response({"items": [{"id": "repo-1", "name": "repo"}]})
        if method == "GET" and "/models?name=" in url:
            return _response({"items": self.models})
        if method == "POST" and url.endswith("/models"):
            model = {"id": "model-1", **(json_body or {})}
            self.models.append(model)
            return _response(model)
        if method == "GET" and "/versions?registrationFingerprint=" in url:
            return _response({"items": self.versions})
        if method == "POST" and url.endswith("/versions"):
            version = {"id": "version-1", **(json_body or {})}
            self.versions.append(version)
            return _response(version)
        if method == "PUT" and url.endswith("/metadata"):
            return _response(json_body or {})
        if method == "GET" and "/versions/version-1" in url:
            return _response({"customProperties": comparable_metadata(_package())})
        return _response({})


def _config(tmp_path: Path) -> tuple[LifecycleConfig, RegistrationConfig]:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    payload = config.model_dump()
    payload["provider"]["selected"] = "sas_viya"
    payload["sas_viya"]["enabled"] = True
    payload["sas_viya"]["authentication_mode"] = "none"
    updated = LifecycleConfig.model_validate(payload)
    registration = RegistrationConfig(
        linkage_path=tmp_path / "linkage.json",
        evidence_directory=tmp_path / "evidence",
    )
    return updated, registration


def _package() -> Any:
    return build_model_package(LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")))


def _response(payload: dict[str, Any]) -> HttpResponse:
    import json

    return HttpResponse(200, json.dumps(payload), {})


def test_sas_viya_registration_is_idempotent(tmp_path: Path) -> None:
    config, registration = _config(tmp_path)
    transport = RegistrationTransport()
    provider = SasViyaLifecycleProvider(
        config.sas_viya,
        registration_config=registration,
        transport=transport,
    )
    package = build_model_package(config)

    first = provider.register_model_package(package)
    second = provider.register_model_package(package)

    assert first.registration_status == "registered"
    assert second.registration_status == "already_registered"
    assert len([call for call in transport.calls if call["method"] == "POST"]) == 2
    assert (tmp_path / "linkage.json").is_file()
    assert first.evidence_path is not None
    evidence_text = next((tmp_path / "evidence").glob("*.json")).read_text(encoding="utf-8")
    assert "Authorization" not in evidence_text
    assert "SAS_VIYA_ACCESS_TOKEN" not in evidence_text


def test_sas_viya_dry_run_makes_no_http_calls(tmp_path: Path) -> None:
    config, registration = _config(tmp_path)
    transport = RegistrationTransport()
    provider = SasViyaLifecycleProvider(
        config.sas_viya,
        registration_config=registration,
        transport=transport,
    )

    result = provider.register_model_package(build_model_package(config), dry_run=True)

    assert result.registration_status == "reconciled"
    assert result.metadata_synchronisation_status == "not_attempted"
    assert transport.calls == []
