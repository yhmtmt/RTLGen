# Evaluation Gate

- Run only after this implementation and proposal merge.
- Measure all six Nangate45 points: 1.0/1.5 ns crossed with 40/50/60 percent
  core utilization.
- Accept physically completed rows or explicit bounded flow failures.
- Audit post-synthesis retention of all four descriptor entries, eight
  outstanding metadata entries, and eight RX contexts.
- Require registered external data inputs and report startpoint/endpoint path
  identity for any non-monotonic timing result before promotion.
- Report endpoint-control-plus-harness area/power/timing. Do not classify the
  result as SRAM macro, router, aggregate mesh, or workload-activity evidence.
