# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-19T11:35:00Z
- scope:
  - keep the first remote stage focused on Layer 1 physical implementation
    evidence only
  - keep the first pass focused on a bounded `int8` sigmoid block
  - do not mix in Layer 2 perf campaigns yet
- blocked_on:
  - choosing the bounded `int8` sigmoid implementation path
  - fixing the first-pass `pwl` point set for the sigmoid approximation
  - defining the target wrapper contract and local smoke checks
