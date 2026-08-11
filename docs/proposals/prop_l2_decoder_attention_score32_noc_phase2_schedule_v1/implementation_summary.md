# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- Score32 segmented-mesh Phase 2 L2 dispatch

## Scope
- Added an exact-item L2 generator path for the full 8-wave, 128-tile routed
  schedule.
- Added bounded remote resources, exact outputs, proposal linkage, and explicit
  remaining-abstraction acceptance checks.
- Corrected compute-to-NoC clock conversion after the unrun v1 contract was
  found to interpret `48.6509 ns` compute-wrapper cycles as router cycles.
- Added idle fast-forward that preserves absolute cycle timestamps, allowing
  physically spaced releases without storing hundreds of thousands of empty
  traces.
- Did not alter router RTL, source traffic quantities, or HBM.

## Files Changed
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- `npu/sim/perf/noc_segmented_mesh.py`
- `npu/eval/measure_llm_decoder_attention_score32_noc_phase2_schedule.py`
- `tests/test_noc_segmented_mesh.py`
- `tests/test_llm_decoder_attention_score32_noc_phase2_schedule.py`
- this proposal workspace

## Local Validation
- Focused L2 generator tests: 2 passed.
- NoC simulator/materializer tests cover absolute clock conversion and idle
  fast-forward equivalence in addition to routing and tag safety.
- `python3 scripts/validate_runs.py --skip_eval_queue`: passed.
- `git diff --check`: passed.

## Evaluation Request
- One immutable low-cost evidence-only remote L2 retry; the unrun v1 item is
  superseded and must not be consumed.
- Compare routed service evidence against the prior scalar NoC assumption.

## Risks
- The result cannot close HBM/DRAM, physical SRAM placement, root-finalizer
  compute, or producer descriptor/control storage.
- The explicit 1ns NoC target remains an assumption until the segmented-router
  physical item supplies a measured clock.
