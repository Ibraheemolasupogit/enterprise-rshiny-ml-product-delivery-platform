from pathlib import Path
from typing import Any

import pytest

from ml_product.lifecycle.config import LifecycleConfig, SasViyaConfig
from ml_product.lifecycle.sas_viya_client import (
    HttpResponse,
    SasViyaApiError,
    SasViyaAuthenticationError,
    SasViyaClient,
    SasViyaConnectivityError,
)


class FakeTransport:
    def __init__(
        self,
        response: HttpResponse | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.response = response or HttpResponse(200, "{\"status\":\"UP\"}", {})
        self.error = error
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
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "verify": verify,
                "json_body": json_body,
            }
        )
        if self.error is not None:
            raise self.error
        return self.response


def _sas_config(mode: str = "bearer_token") -> SasViyaConfig:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    payload = config.sas_viya.model_dump()
    payload["authentication_mode"] = mode
    return SasViyaConfig.model_validate(payload)


def test_bearer_auth_header_uses_environment_without_logging_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAS_VIYA_ACCESS_TOKEN", "super-secret-token")
    client = SasViyaClient(_sas_config())

    headers = client.build_auth_headers()

    assert headers == {"Authorization": "Bearer super-secret-token"}


def test_missing_bearer_token_error_does_not_expose_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAS_VIYA_ACCESS_TOKEN", raising=False)
    client = SasViyaClient(_sas_config())

    with pytest.raises(SasViyaAuthenticationError) as exc:
        client.build_auth_headers()

    assert "SAS_VIYA_ACCESS_TOKEN" in str(exc.value)
    assert "Bearer" not in str(exc.value)


def test_readiness_success_uses_injected_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAS_VIYA_ACCESS_TOKEN", "local-token")
    transport = FakeTransport()
    client = SasViyaClient(_sas_config(), transport=transport)

    result = client.readiness_check()

    assert result["healthy"] is True
    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["headers"]["Authorization"] == "Bearer local-token"


def test_api_failure_maps_to_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAS_VIYA_ACCESS_TOKEN", "local-token")
    transport = FakeTransport(HttpResponse(503, "{\"status\":\"DOWN\"}", {}))
    client = SasViyaClient(_sas_config(), transport=transport)

    with pytest.raises(SasViyaApiError, match="HTTP status 503"):
        client.readiness_check()


def test_transport_timeout_maps_to_connectivity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAS_VIYA_ACCESS_TOKEN", "local-token")
    client = SasViyaClient(_sas_config(), transport=FakeTransport(error=TimeoutError()))

    with pytest.raises(SasViyaConnectivityError, match="not reachable"):
        client.readiness_check()
