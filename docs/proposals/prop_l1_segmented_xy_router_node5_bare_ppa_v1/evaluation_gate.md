# Evaluation Gate

- Status: pending human approval; source and dependencies are ready.
- Router r7 is promoted. Generate only from the clean pinned source (or an
  exact clean descendant) when the evaluator has no conflicting active run.
- Measure 40, 50, and 60 percent utilization at 1.8 ns with independent ORFS
  result directories.
- Require complete timing, die area, and power for promotable rows.
- Retain path identity and explicit failures; do not substitute router-plus-
  harness PPA or claim aggregate mesh closure.
- Preserve routed netlist/DEF/reports for the matching post-route VCD power job.

Local verification on 2026-09-05 passed 9 focused bare-router,
activity-generation, post-route-audit, and task-plumbing tests. This is source
readiness evidence only; it is not routed PPA or activity-power evidence.
