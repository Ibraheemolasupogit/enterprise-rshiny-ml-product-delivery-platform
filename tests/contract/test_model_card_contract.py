from pathlib import Path


def test_model_card_contract() -> None:
    text = Path("reports/model_evaluation/model_card.md").read_text(encoding="utf-8")
    assert "Model registration: implemented locally" in text
    assert "Model serving: implemented locally" in text
    assert "R-Shiny integration: implemented locally" in text
    assert "Production approval: not granted" in text
    assert "Deployment: not performed" in text
