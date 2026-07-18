"""Typed SAS Viya client boundary for lifecycle integration."""

from __future__ import annotations

import base64
import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from ml_product.lifecycle.config import SasViyaConfig


class SasViyaError(RuntimeError):
    """Base exception for SAS Viya lifecycle integration failures."""


class SasViyaConfigurationError(SasViyaError):
    """Raised when the SAS Viya client is not safely configured."""


class SasViyaAuthenticationError(SasViyaError):
    """Raised when required SAS Viya authentication material is unavailable."""


class SasViyaConnectivityError(SasViyaError):
    """Raised when the SAS Viya endpoint cannot be reached."""


class SasViyaApiError(SasViyaError):
    """Raised when SAS Viya returns an unsuccessful response."""


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    text: str
    headers: dict[str, str]

    def json(self) -> dict[str, Any]:
        payload = json.loads(self.text or "{}")
        if not isinstance(payload, dict):
            raise SasViyaApiError("SAS Viya response must be a JSON object.")
        return payload


class HttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        timeout: int,
        verify: bool,
        json_body: dict[str, Any] | None = None,
    ) -> HttpResponse: ...


class UrllibTransport:
    """Small stdlib HTTP transport used when tests do not inject a fake transport."""

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
        body = None
        request_headers = dict(headers)
        if json_body is not None:
            body = json.dumps(json_body, sort_keys=True).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        context = ssl.create_default_context()
        if not verify:
            context = ssl._create_unverified_context()  # noqa: S323
        request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                text = response.read().decode("utf-8")
                return HttpResponse(
                    status_code=response.status,
                    text=text,
                    headers=dict(response.headers.items()),
                )
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return HttpResponse(status_code=exc.code, text=text, headers=dict(exc.headers.items()))
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise SasViyaConnectivityError("SAS Viya endpoint is not reachable.") from exc


class SasViyaClient:
    """Minimal live-client boundary with injectable transport and no committed secrets."""

    def __init__(
        self,
        config: SasViyaConfig,
        *,
        transport: HttpTransport | None = None,
    ) -> None:
        self.config = config
        self.transport = transport or UrllibTransport()

    def build_auth_headers(self) -> dict[str, str]:
        mode = self.config.authentication_mode
        if mode == "none":
            return {}
        if mode == "bearer_token":
            token = os.environ.get(self.config.access_token_env)
            if not token:
                raise SasViyaAuthenticationError(
                    f"Missing SAS Viya access token environment variable: "
                    f"{self.config.access_token_env}"
                )
            return {"Authorization": f"Bearer {token}"}
        if mode == "client_credentials":
            client_id = os.environ.get(self.config.client_id_env)
            client_secret = os.environ.get(self.config.client_secret_env)
            missing = [
                name
                for name, value in (
                    (self.config.client_id_env, client_id),
                    (self.config.client_secret_env, client_secret),
                )
                if not value
            ]
            if missing:
                raise SasViyaAuthenticationError(
                    "Missing SAS Viya client credential environment variable(s): "
                    + ", ".join(missing)
                )
            credential = f"{client_id}:{client_secret}".encode()
            encoded = base64.b64encode(credential).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        raise SasViyaConfigurationError(f"Unsupported SAS Viya authentication mode: {mode}")

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._url(path)
        try:
            response = self.transport.request(
                method,
                url,
                headers=self.build_auth_headers(),
                timeout=self.config.timeout_seconds,
                verify=self.config.verify_tls,
                json_body=json_body,
            )
        except SasViyaError:
            raise
        except Exception as exc:
            raise SasViyaConnectivityError("SAS Viya endpoint is not reachable.") from exc
        if response.status_code >= 400:
            raise SasViyaApiError(
                f"SAS Viya API request failed with HTTP status {response.status_code}."
            )
        return response.json()

    def readiness_check(self) -> dict[str, Any]:
        payload = self.request("GET", self.config.readiness_path)
        return {
            "provider": "sas_viya",
            "provider_label": self.config.provider_label,
            "healthy": True,
            "endpoint": self.config.readiness_path,
            "response": payload,
        }

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            raise SasViyaConfigurationError("SAS Viya API path must start with /.")
        return f"{self.config.base_url}{path}"
