from pathlib import Path


def test_database_validation_sql_files_exist() -> None:
    assert len(list(Path("database/validation").glob("*.sql"))) >= 6


def test_no_real_denodo_evidence_created() -> None:
    evidence_files = [path for path in Path("denodo/evidence").glob("*") if path.name != ".gitkeep"]

    assert evidence_files == []
