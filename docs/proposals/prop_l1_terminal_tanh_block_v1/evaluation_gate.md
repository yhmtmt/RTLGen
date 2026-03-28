# Evaluation Gate

- status: approved
- approved_by: user
- approved_utc: 2026-03-24T12:00:00Z
- scope:
  - keep the first remote stage focused on Layer 1 physical implementation evidence only
  - keep the first pass focused on one bounded `int8` tanh block
  - do not mix in integrated `nm1` or Layer 2 perf campaigns yet
- blocked_on:
  - implementing the bounded tanh block and local smoke checks
  - executing the staged Nangate45 physical sweep
  - reviewing the resulting `metrics.csv` rows and accepted seed choice
