import pytest
from pydantic import ValidationError

from ml_product.serving.schemas import PredictionRequest
from tests.unit.serving.test_utils import sample_request_payload


def test_prediction_request_accepts_raw_fields() -> None:
    request = PredictionRequest.model_validate(sample_request_payload())
    assert request.age == 72


def test_prediction_request_rejects_outcome_fields() -> None:
    payload = sample_request_payload()
    payload["long_stay_flag"] = True
    with pytest.raises(ValidationError, match="Outcome or identifier"):
        PredictionRequest.model_validate(payload)
