from pytest import MonkeyPatch

from scripts import validate_repository


def test_checkout_safe_mode_omits_generated_artifact_checks(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        validate_repository,
        "validate_model_foundation",
        lambda: ["generated model artefact missing"],
    )

    assert validate_repository.run({"checkout_safe"}) == 0
    assert validate_repository.run({"models"}) == 1
