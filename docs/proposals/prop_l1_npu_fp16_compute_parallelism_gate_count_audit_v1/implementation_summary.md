# Implementation Summary

## Current State
- `run_block_sweep.py` now accepts finish/final/place/route/synth variants of
  OpenROAD instance area, stdcell area, and stdcell count metric keys.
- The local RTL/Yosys sanity check confirmed generated MAC instance counts of
  1, 2, 4, 8, and 16 before flattening for nm1 through nm16.

## First Evaluation Plan
- Dispatch one Layer 1 sweep item for nm1, nm2, nm4, nm8, and nm16.
- Use the existing cmp33 `mode_compare` sweep so the audit remains comparable
  with the current stability results.
- Accept the result only if metrics rows contain populated physical cell/area
  columns.

## Expected Deliverable
- A lightweight metrics-only PR with one row per wrapper/mode.
- A conclusion stating whether `nm4` can be interpreted as a retained-logic
  physical result or should be discarded as suspect.
