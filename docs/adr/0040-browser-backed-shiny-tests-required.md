# ADR 0040: Browser Backed Shiny Tests Required

Status: Accepted

Context: Unit tests cannot verify complete Shiny navigation and browser behaviour.

Decision: Milestone 10 keeps `shinytest2` browser-backed tests in the quality path and CI.

Consequences: A runnable Chrome or Chromium runtime is required for complete local validation.

Alternatives considered: Skipping browser tests was rejected because it would leave product navigation untested.
