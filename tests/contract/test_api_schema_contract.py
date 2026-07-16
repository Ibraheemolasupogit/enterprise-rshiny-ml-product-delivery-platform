from tests.unit.serving.test_utils import sample_request_payload


def test_api_schema_sample_contains_no_outcomes_or_identifiers() -> None:
    payload = sample_request_payload()
    prohibited = {"patient_id", "admission_id", "long_stay_flag", "length_of_stay_days"}
    assert prohibited.isdisjoint(payload)
