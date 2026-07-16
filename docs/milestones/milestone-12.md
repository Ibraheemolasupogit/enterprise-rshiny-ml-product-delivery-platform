# Milestone 12: Controlled Retraining and Champion-Challenger Review

Status: Complete.

Milestone 12 adds a controlled local retraining workflow for synthetic evidence. It assesses monitoring review eligibility, prepares a labelled retraining dataset, preserves grouped temporal splitting, fits preprocessing on retraining train only, trains deterministic challenger families, scores the registered champion, compares champion and challenger metrics, reviews fairness and stability, evaluates promotion gates, and writes a human-readable recommendation.

The representative committed recommendation is `retain_champion`. This is intentional and valid: the milestone proves controlled evaluation without forcing a challenger to win.

No model is approved, activated, deployed or replaced. The real registry remains unchanged by default, and registration-for-review is a separate explicit command that is blocked unless evidence recommends challenger registration review.
