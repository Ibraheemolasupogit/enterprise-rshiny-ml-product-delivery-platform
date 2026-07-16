from pathlib import Path

import duckdb


def test_curated_views_have_expected_counts() -> None:
    connection = duckdb.connect("data/processed/ml_product.duckdb", read_only=True)
    try:
        assert (
            connection.execute("select count(*) from curated.model_source_view").fetchone()[0]
            == 117
        )
        assert (
            connection.execute(
                "select count(*) from curated.daily_ward_operational_context"
            ).fetchone()[0]
            == 360
        )
        assert (
            connection.execute(
                "select count(*) from curated.admission_operational_context "
                "where context_match_type='exact_date'"
            ).fetchone()[0]
            == 117
        )
    finally:
        connection.close()


def test_database_file_is_generated_not_committed() -> None:
    assert Path("data/processed/ml_product.duckdb").exists()
