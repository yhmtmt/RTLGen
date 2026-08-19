# Implementation Summary

- Added a bounded 768-bit-reservoir exact stats-once encoder and decoder.
- Added independent randomized round-trip and malformed-protocol tests.
- Added a matched PPA harness with one canonical group source, deterministic
  stalls, exact decoded-beat comparison, and an all-bit observation fold.
- Added constant-elaborated aligned and stats-once generated PPA tops.
- Added a paired Nangate45 sweep over 1.0/1.5/2.0 ns and 40/50/60 percent
  utilization at placement density 0.52.

Local verification: 13 focused tests pass and `validate_runs.py
--skip_eval_queue` passes. Yosys removes the unselected codec hierarchy and
contains no multiplier cells in the matched source support.
