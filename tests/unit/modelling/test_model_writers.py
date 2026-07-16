from pathlib import Path

from ml_product.modelling.writers import prepare_directory, write_json


def test_writer_outputs_json(tmp_path: Path) -> None:
    prepare_directory(tmp_path, replace=True)
    write_json(tmp_path / "evidence.json", {"ok": True})
    assert "ok" in (tmp_path / "evidence.json").read_text(encoding="utf-8")
