# Quality Gate

## Status
- status: pending

## Required Checks
- define whether the first-pass terminal-op family needs numerical equivalence
  or tolerance-based checking
- define the minimal local regression needed before any remote paired
  comparison is queued

## Notes
- if the chosen terminal-op family remains inside a numerically stable imported
  classifier-tail subset, the gate may stay lightweight
- if the family introduces a new activation or normalization tail, expect a
  stricter quality gate before remote spend
