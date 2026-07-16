# 0027 Local Review Mode Is Not Production Serving

Status: Accepted

Context: Tests need to exercise prediction before the real model is approved.

Decision: Review mode is disabled by default, allowed only locally, and labelled as unapproved and not for operational use.

Consequences: Integration tests can score the registered candidate without making production claims.

Alternatives considered: Approving the real candidate for test convenience was rejected.
