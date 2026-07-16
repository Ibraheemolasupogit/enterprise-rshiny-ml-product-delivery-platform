# R-Shiny MVP Report

Milestone 9 implements a modular R-Shiny MVP that consumes the governed local
FastAPI scoring service.

The application includes Product Overview, Single Prediction and User Feedback
pages only for the Milestone 9 view. Later milestones add cohort scoring,
performance, governance and monitoring pages, but never registry administration,
retraining, rollback or release controls.

The registered model remains unapproved and inactive. Operational serving is
unavailable. Local review mode is the only demonstration scoring path and every
prediction is labelled as review mode, unapproved, synthetic and not for
operational or clinical use.
