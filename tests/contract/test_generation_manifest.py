import json
from pathlib import Path


def test_generation_manifest_has_required_metadata() -> None:
    manifest = json.loads(Path("data/sample/generation_manifest.json").read_text(encoding="utf-8"))

    assert manifest["dataset_version"] == "0.2.0"
    assert manifest["seed"] == 20260714
    assert manifest["configuration_fingerprint"]
    assert "synthetic" in manifest["synthetic_data_declaration"].lower()
    assert manifest["total_issue_count"] > 0


def test_generation_manifest_checksums_reference_files() -> None:
    manifest = json.loads(Path("data/sample/generation_manifest.json").read_text(encoding="utf-8"))

    for file_group in manifest["files"].values():
        for metadata in file_group.values():
            assert Path(metadata["path"]).is_file()
            assert len(metadata["checksum_sha256"]) == 64
