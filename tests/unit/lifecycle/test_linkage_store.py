from pathlib import Path

from ml_product.lifecycle.linkage import LinkageStore
from ml_product.lifecycle.models import LinkageRecord


def _record(version: int = 1) -> LinkageRecord:
    return LinkageRecord(
        provider="sas_viya",
        local_model_id="MODEL-REG-000001",
        local_model_version=version,
        local_build_identifier="CAND-1",
        registration_fingerprint="abc123",
        external_project_id="repo-1",
        external_model_id="model-1",
        external_model_version_id="version-1",
        metadata_sync_status="synchronised",
        first_registered_at_utc="2026-07-18T00:00:00+00:00",
        last_reconciled_at_utc="2026-07-18T00:00:00+00:00",
        evidence_checksum="checksum",
    )


def test_linkage_store_upsert_is_idempotent(tmp_path: Path) -> None:
    store = LinkageStore(tmp_path / "linkage.json")

    store.upsert(_record())
    store.upsert(_record(version=1))

    payload = store.load()
    assert len(payload.records) == 1
    assert payload.records[0].registration_fingerprint == "abc123"
