from pathlib import Path

from ml_product.ingestion.build import build_database
from ml_product.ingestion.config import DatabaseConfig


def test_database_build_pipeline_temp_database(tmp_path: Path) -> None:
    config = DatabaseConfig.from_file(Path("config/database.yaml")).with_overrides(
        database_path=tmp_path / "test.duckdb",
        replace=True,
    )

    result = build_database(config)

    assert result.database_path.exists()
    assert result.build_id.startswith("DBUILD-")
    assert result.counts["raw.patients"] == 81
    assert result.counts["quality.data_quality_issues"] == 9
    assert result.counts["quality.rejected_records"] == 4
