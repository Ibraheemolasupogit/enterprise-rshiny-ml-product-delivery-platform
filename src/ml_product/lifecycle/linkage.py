"""Local linkage/evidence store for external lifecycle registrations."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from ml_product.lifecycle.models import LinkageRecord, LinkageStorePayload
from ml_product.utils.paths import repository_root


class LinkageStore:
    def __init__(self, path: Path) -> None:
        self.path = path if path.is_absolute() else repository_root() / path

    def load(self) -> LinkageStorePayload:
        if not self.path.is_file():
            return LinkageStorePayload()
        return LinkageStorePayload.model_validate(
            json.loads(self.path.read_text(encoding="utf-8"))
        )

    def find(self, provider: str, registration_fingerprint: str) -> LinkageRecord | None:
        for record in self.load().records:
            if (
                record.provider == provider
                and record.registration_fingerprint == registration_fingerprint
            ):
                return record
        return None

    def upsert(self, record: LinkageRecord) -> None:
        payload = self.load()
        records = [
            existing
            for existing in payload.records
            if not (
                existing.provider == record.provider
                and existing.registration_fingerprint == record.registration_fingerprint
            )
        ]
        records.append(record)
        records.sort(key=lambda item: (item.provider, item.registration_fingerprint))
        self.write(LinkageStorePayload(records=records))

    def write(self, payload: LinkageStorePayload) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = payload.model_dump_json(indent=2) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            delete=False,
        ) as handle:
            handle.write(text)
            temp_path = Path(handle.name)
        temp_path.replace(self.path)


def sha256_json(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
