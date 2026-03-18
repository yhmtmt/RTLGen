# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-18T14:05:00Z
- scope:
  - first remote stage must remain `measurement_only`
  - second remote stage may use `paired_comparison` only after local legality
    and quality checks are in place
- blocked_on:
  - queueing the first `measurement_only` standalone terminal `Relu` suite item
  - accepting the measurement evidence and deciding whether the paired stage
    needs any extra quality gate beyond schedule and perf artifacts
