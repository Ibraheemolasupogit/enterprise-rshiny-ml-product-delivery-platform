from ml_product.linking.deterministic_linker import admission_context_key, unresolved_foreign_keys
from ml_product.linking.duplicate_detector import duplicate_keys
from ml_product.linking.linkage_quality import linkage_metrics


def test_admission_context_key_uses_ward_and_admission_date() -> None:
    assert admission_context_key(
        {"ward_id": "WARD-01", "admission_datetime": "2025-01-02T03:30"}
    ) == ("WARD-01", "2025-01-02")


def test_duplicate_and_unresolved_helpers() -> None:
    assert duplicate_keys([{"id": "A"}, {"id": "A"}, {"id": "B"}], "id") == ["A"]
    assert unresolved_foreign_keys(
        [{"fk": "A"}, {"fk": "C"}], child_key="fk", parent_keys={"A"}
    ) == ["C"]
    assert linkage_metrics(total=4, matched=3)["unmatched_records"] == 1
