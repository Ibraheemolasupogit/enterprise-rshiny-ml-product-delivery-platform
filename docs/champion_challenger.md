# Champion-Challenger Evaluation

Champion-challenger evaluation compares the registered champion and retrained challengers on the same challenger-validation records. It records PR-AUC, ROC-AUC, Brier score, log loss, recall, precision, specificity, F1, balanced accuracy, calibration error and weighted operational cost.

Metric directions are explicit: higher PR-AUC and ROC-AUC are better, while lower Brier score, log loss and weighted cost are better. The historical locked test set is not used for challenger selection or threshold tuning.

The representative Milestone 12 evidence retains the champion because gate results are conditional and the champion-preference rule applies when differences are not sufficiently meaningful.
