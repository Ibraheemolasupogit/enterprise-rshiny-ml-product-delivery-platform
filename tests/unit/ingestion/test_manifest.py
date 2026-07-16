from pathlib import Path

from ml_product.ingestion.manifest import build_identifier, validate_source_manifest


def test_source_manifest_validates() -> None:
    manifest = validate_source_manifest(Path("data/sample"), preferred_format="parquet")

    assert manifest["dataset_version"] == "0.2.0"
    assert manifest["configuration_fingerprint"]


def test_build_identifier_is_stable() -> None:
    assert build_identifier("abc", "1") == build_identifier("abc", "1")
