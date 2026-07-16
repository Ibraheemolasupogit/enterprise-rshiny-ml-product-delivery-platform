from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ml_product.serving.app import create_app
from tests.unit.serving.test_utils import sample_request_payload


def test_api_liveness_public_and_default_not_ready() -> None:
    client = TestClient(create_app(root=Path(".")))
    assert client.get("/health/live").status_code == 200
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["ready"] is False


def test_prediction_requires_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "local-test-key")
    client = TestClient(create_app(root=Path(".")))
    response = client.post("/v1/predict", json=sample_request_payload())
    assert response.status_code == 401


def test_prediction_unavailable_without_active_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "local-test-key")
    client = TestClient(create_app(root=Path(".")))
    response = client.post(
        "/v1/predict",
        json=sample_request_payload(),
        headers={"X-API-Key": "local-test-key"},
    )
    assert response.status_code == 503
