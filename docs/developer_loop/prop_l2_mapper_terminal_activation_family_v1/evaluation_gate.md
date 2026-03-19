# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:20:00Z
- scope:
  - prerequisite first remote stage is a Layer 1 physical sweep for a bounded
    terminal `int8` sigmoid block
  - first Layer 2 remote stage must remain `measurement_only`
  - second remote stage may use `paired_comparison` only after:
    - the Layer 1 `int8` sigmoid block is accepted and merged
    - local legality checks pass
    - local quality gate is accepted
    - the baseline evidence PR is merged and materialized
- blocked_on:
  - promoting and implementing `prop_l1_terminal_sigmoid_block_v1`
  - choosing whether the first Layer 2 family stays `Sigmoid` only or adds a
    second nonlinear member later after the `int8` block is accepted
  - defining the quality-gate thresholds and local checks
