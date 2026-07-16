import json
from pathlib import Path


def test_champion_challenger_contract() -> None:
    payload = json.loads(
        Path("reports/retraining/champion_challenger_comparison.json").read_text(encoding="utf-8")
    )
    assert payload["same_row_evaluation_confirmation"] is True
    assert payload["historical_test_set_used_for_selection"] is False
    champion = payload["champion"]
    assert champion["candidate_identifier"] == "CAND-85EA9202CAD6FE7F"
    assert len(payload["challengers"]) == 3
    for row in payload["challengers"]:
        assert row["schema_compatible"] is True
        assert row["reproducible"] is True
