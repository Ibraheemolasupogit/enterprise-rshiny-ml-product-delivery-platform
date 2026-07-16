# First Commit Runbook

Future manual sequence:

```bash
git status --short
git add .
git status --short
git commit -m "feat: build enterprise R-Shiny ML product delivery platform"
git push -u origin main
```

Before `git add`, review generated and untracked files carefully, confirm ignored artefacts are absent, confirm secrets are excluded, and confirm model binaries are not staged. The initial commit will activate GitHub Actions after push. Remote CI results must be reviewed after push. Do not create a release until remote CI is green. Operational release remains blocked regardless of CI because the model is unapproved and inactive.
