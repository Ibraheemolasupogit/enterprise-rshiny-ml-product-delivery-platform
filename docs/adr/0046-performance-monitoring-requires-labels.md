# ADR 0046: Performance Monitoring Requires Labels

## Status

Accepted.

## Context

Model performance metrics such as recall, specificity, ROC-AUC and calibration require observed outcomes. Unlabelled monitoring windows can only support distribution checks.

## Decision

Performance monitoring runs only when labels are present and minimum sample requirements are met. Otherwise the section reports insufficient evidence and directs reviewers to labelled follow-up.

## Consequences

The monitoring layer avoids false certainty. Prediction drift can still trigger review, but labelled performance evidence is required before performance degradation is reported.
