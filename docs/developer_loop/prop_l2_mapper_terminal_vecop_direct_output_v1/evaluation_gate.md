# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-18T14:05:00Z
- scope:
  - first remote stage remains the accepted `measurement_only` baseline from
    PR `#58`
  - second remote stage may use `paired_comparison` now that the baseline
    evidence and local vec-op direct-output legality checks are in place
- blocked_on:
  - queueing the paired direct-output vs non-fused standalone terminal `Relu`
    suite item
  - confirming that the paired item exports schedule and perf evidence for all
    suite models, not just a single representative row
