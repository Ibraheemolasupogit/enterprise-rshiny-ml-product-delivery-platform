from pathlib import Path


def test_governed_view_sql_has_no_select_star() -> None:
    for path in Path("database/views").glob("*.sql"):
        assert "select *" not in path.read_text(encoding="utf-8").lower(), path


def test_model_source_view_does_not_encode_or_scale_features() -> None:
    text = Path("database/views/150_model_source_view.sql").read_text(encoding="utf-8").lower()

    assert "one_hot" not in text
    assert "scale(" not in text
    assert "train" not in text
