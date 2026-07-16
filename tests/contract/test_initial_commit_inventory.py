import json
from pathlib import Path


def test_initial_commit_inventory_is_eligible() -> None:
    payload = json.loads(
        Path("reports/portfolio/initial_commit_inventory.json").read_text(encoding="utf-8")
    )
    assert payload["commit_eligible"] is True
    assert payload["unexpected_files"] == []
    assert payload["large_files"] == []
    assert payload["binary_files"] == []
    assert payload["secrets_result"] == "passed"
    assert payload["absolute_path_result"] == "passed"
