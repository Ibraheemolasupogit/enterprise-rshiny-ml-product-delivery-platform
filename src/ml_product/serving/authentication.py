"""Local API-key authentication."""

from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request, status

from ml_product.serving.config import ServingConfig


def require_api_key(config: ServingConfig, request: Request) -> None:
    expected = os.environ.get(config.security.api_key_environment_variable)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key environment variable is not configured.",
        )
    api_key = request.headers.get("X-API-Key")
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key.")
    if not hmac.compare_digest(api_key, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key.")
