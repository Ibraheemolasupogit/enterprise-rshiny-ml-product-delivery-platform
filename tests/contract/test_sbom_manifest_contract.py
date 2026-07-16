import json
from pathlib import Path


def test_sbom_manifest_contract() -> None:
    payload = json.loads(Path("reports/assurance/sbom_manifest.json").read_text(encoding="utf-8"))
    names = {entry["artefact_name"] for entry in payload["sboms"]}
    assert {"repository-filesystem", "api-image", "rshiny-image"}.issubset(names)
    assert payload["publication_status"] == "not_published"
