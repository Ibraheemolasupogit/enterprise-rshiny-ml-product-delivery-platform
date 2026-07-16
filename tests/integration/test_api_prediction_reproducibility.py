from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ml_product.serving.app import create_app
from ml_product.serving.config import ServingConfig
from tests.unit.serving.test_utils import sample_request_payload


def test_review_prediction_is_deterministic(
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
    headers = {"X-API-Key": "local-test-key"}
    first = client.post("/v1/predict", json=sample_request_payload(), headers=headers).json()
    second = client.post("/v1/predict", json=sample_request_payload(), headers=headers).json()
    assert first["prediction"] == second["prediction"]
    assert first["model"] == second["model"]
