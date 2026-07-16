import json
import re
from pathlib import Path


def is_revision_or_uncommitted(value: str) -> bool:
    return value == "uncommitted" or re.fullmatch(r"[0-9a-f]{40}", value) is not None


def test_release_manifest_contract() -> None:
    payload = json.loads(
        Path("reports/assurance/release_manifest.json").read_text(encoding="utf-8")
    )
    assert payload["milestone"] == 13
    assert payload["remote_ci_executed"] is False
    assert is_revision_or_uncommitted(payload["git_revision"])
    assert payload["publish_images"] is False
    assert payload["external_deployment_enabled"] is False
    assert payload["cloud_deployment_enabled"] is False
