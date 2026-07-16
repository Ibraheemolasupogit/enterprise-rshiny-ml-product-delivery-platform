# Data Quality Treatment

Milestone 3 reconciles intentional Milestone 2 quality fixtures. It does not silently repair source data.

| Issue | Raw | Staged | Curated |
| --- | --- | --- | --- |
| Missing deprivation decile | Preserve | Preserve with quality flag | Include where permitted |
| Missing mobility status | Preserve | Preserve with quality flag | Include with quality status |
| Duplicate patient | Preserve | Identify duplicate | Exclude duplicate key from trusted curated joins |
| Duplicate admission | Preserve | Identify duplicate | Exclude duplicate key from trusted curated joins |
| Orphan diagnosis | Preserve | Quarantine | Exclude from diagnosis summary |
| Inconsistent long-stay flag | Preserve | Preserve source and compute governed value | Expose both source and governed values |
| Occupied beds greater than staffed beds | Preserve | Mark accepted operational exception | Include with exception flag |
| Vacancy rate outside range | Preserve | Flag as intentional fixture | Exclude invalid metric from trusted operational view |

The committed sample has nine issues and all nine are reconciled in `quality.data_quality_issues`.
