from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ml_product.serving.app import create_app
from ml_product.serving.config import ServingConfig
from tests.unit.serving.test_utils import sample_request_payload


def test_review_mode_prediction_is_labelled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "local-test-key")
    monkeypatch.setenv("SERVING_REVIEW_MODE", "true")
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    config = config.model_copy(
        update={
            "logging": config.logging.model_copy(
                update={"event_log_path": tmp_path / "prediction_events.jsonl"}
            )
        }
    )
    client = TestClient(create_app(serving_config=config, root=Path(".")))
    response = client.post(
        "/v1/predict",
        json=sample_request_payload(),
        headers={"X-API-Key": "local-test-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0.0 <= payload["prediction"]["long_stay_probability"] <= 1.0
    assert payload["request"]["review_mode"] is True
    assert "unapproved_model" in payload["request"]["status"]
    assert payload["model"]["approval_status"] == "pending"
    assert payload["model"]["activation_status"] == "inactive"


def test_review_mode_batch_prediction_preserves_order_and_labels(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "local-test-key")
    monkeypatch.setenv("SERVING_REVIEW_MODE", "true")
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    config = config.model_copy(
        update={
            "logging": config.logging.model_copy(
                update={"event_log_path": tmp_path / "prediction_events.jsonl"}
            )
        }
    )
    client = TestClient(create_app(serving_config=config, root=Path(".")))
    first = sample_request_payload()
    second = sample_request_payload()
    first["request_id"] = "BATCH-001"
    second["request_id"] = "BATCH-002"
    second["age"] = 81
    response = client.post(
        "/v1/predict/batch",
        json={"records": [first, second]},
        headers={"X-API-Key": "local-test-key"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["request"]["request_id"] for item in payload] == ["BATCH-001", "BATCH-002"]
    assert len(payload) == 2
    assert {item["model"]["registry_version"] for item in payload} == {1}
    for item in payload:
        assert item["request"]["review_mode"] is True
        assert {"review_mode", "unapproved_model", "not_for_operational_use"}.issubset(
            set(item["request"]["status"])
        )
        assert item["prediction"]["risk_band"] in {"low", "medium", "high"}


def test_batch_prediction_enforces_configured_limit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "local-test-key")
    monkeypatch.setenv("SERVING_REVIEW_MODE", "true")
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    config = config.model_copy(
        update={
            "logging": config.logging.model_copy(
                update={"event_log_path": tmp_path / "prediction_events.jsonl"}
            )
        }
    )
    client = TestClient(create_app(serving_config=config, root=Path(".")))
    records = [sample_request_payload() for _ in range(config.limits.maximum_batch_size + 1)]
    response = client.post(
        "/v1/predict/batch",
        json={"records": records},
        headers={"X-API-Key": "local-test-key"},
    )
    assert response.status_code == 413


def test_review_mode_blocked_outside_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVING_REVIEW_MODE", "true")
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    config = config.model_copy(
        update={"service": config.service.model_copy(update={"environment": "staging"})}
    )
    try:
        create_app(serving_config=config, root=Path("."))
    except ValueError as exc:
        assert "only allowed in the local" in str(exc)
    else:
        raise AssertionError("Review mode should be blocked outside local.")
