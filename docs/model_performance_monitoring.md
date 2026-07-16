# Model Performance Monitoring

Model performance monitoring is evaluated only when current-window outcome labels are present and sufficient. The checks compare labelled metrics such as ROC-AUC, PR-AUC, recall, specificity, Brier score and balanced accuracy with the locked baseline reference.

If labels are missing or too sparse, the performance section returns insufficient evidence rather than inferring degradation from prediction drift. This is an explicit safety boundary for the synthetic product demonstration and prevents unlabelled score movement from becoming an unsupported performance claim.

Performance alerts create a review obligation. They do not perform retraining, challenger selection, promotion, activation, rollback, threshold changes or calibration changes. Any future retraining workflow must be implemented in a separate controlled milestone with human approval.
