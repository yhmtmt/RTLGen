# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:20:00Z
- scope:
  - first remote stage must remain `measurement_only`
  - second remote stage may use `paired_comparison` only after:
    - local legality checks pass
    - local quality gate is accepted
    - the baseline evidence PR is merged and materialized
- blocked_on:
  - choosing the bounded nonlinear activation family
  - defining the quality-gate thresholds and local checks
  - generating the first measurement-only suite and campaign
