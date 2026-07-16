from pathlib import Path

import yaml

WORKFLOWS = {
    "quality.yml",
    "python-tests.yml",
    "r-tests.yml",
    "integration-tests.yml",
    "security.yml",
    "container.yml",
    "release-assurance.yml",
}


def test_required_workflows_are_safe_and_focused() -> None:
    workflow_dir = Path(".github/workflows")
    names = {path.name for path in workflow_dir.glob("*.yml")}
    assert WORKFLOWS.issubset(names)
    for path in workflow_dir.glob("*.yml"):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert payload["permissions"] == {"contents": "read"}
        text = path.read_text(encoding="utf-8").lower()
        assert "write-all" not in text
        assert "docker push" not in text
        assert "gh release" not in text
        assert "deploy" not in path.stem
        assert "activate-model" not in text
        assert "record-approval-decision" not in text
        assert "register-retraining-candidate" not in text


def test_workflow_actions_do_not_use_floating_main() -> None:
    for path in Path(".github/workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "@main" not in text
        assert "@master" not in text
