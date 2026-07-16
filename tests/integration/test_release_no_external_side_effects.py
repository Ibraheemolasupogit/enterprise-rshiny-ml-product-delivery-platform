from pathlib import Path


def test_release_implementation_has_no_external_side_effect_commands() -> None:
    searchable = [
        *Path(".github/workflows").glob("*.yml"),
        Path("Makefile"),
        Path("scripts/smoke_test_local_deployment.sh"),
    ]
    prohibited = [
        "docker push",
        "terraform apply",
        "az deployment",
        "aws cloudformation deploy",
        "gh release create",
        "kubectl apply",
    ]
    for path in searchable:
        text = path.read_text(encoding="utf-8").lower()
        for token in prohibited:
            assert token not in text
