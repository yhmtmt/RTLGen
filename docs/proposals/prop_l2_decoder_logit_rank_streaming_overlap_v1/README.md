# Decoder Logit-Rank Streaming Overlap

This proposal refines the rank-only decoder streaming hierarchy with producer
overlap, candidate FIFO pressure, and byte traffic estimates.

Artifacts:

- `proposal.json`: proposal metadata and review scope
- `evaluation_requests.json`: frontier-detail request
- `design_brief.md`: problem, hypothesis, and equivalence plan
- `evaluation_gate.md`: pending review gate

The model keeps the perf-sim/RTL boundary explicit. A follow-on RTL merge block
must match the same ready/valid stream observables before its PPA can replace
the proxy merge cost.
