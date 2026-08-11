# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- Score32 segmented-mesh Phase 2 L2 dispatch

## Scope
- Added an exact-item L2 generator path for the full 8-wave, 128-tile routed
  schedule.
- Added bounded remote resources, exact outputs, proposal linkage, and explicit
  remaining-abstraction acceptance checks.
- Did not alter router RTL, the simulator, source traffic quantities, or HBM.

## Files Changed
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- this proposal workspace

## Local Validation
- Focused L2 generator tests: 2 passed.
- NoC simulator/materializer tests: 9 passed.
- `python3 scripts/validate_runs.py --skip_eval_queue`: passed.
- `git diff --check`: passed.

## Evaluation Request
- One low-cost evidence-only remote L2 item.
- Compare routed service evidence against the prior scalar NoC assumption.

## Risks
- The result cannot close HBM/DRAM, physical SRAM placement, root-finalizer
  compute, or producer descriptor/control storage.
