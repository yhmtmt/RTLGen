# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_schedule_v1`
- `title`: Score32 segmented-mesh Phase 2 scheduling closure

## Why This Gate Is Required
The result will replace a scalar NoC assumption in later architecture costing.

## Reference
- baseline_ref: checked-in score32 exact-reduction recost artifact
- reference_ref: checked-in measured L1 endpoint-cost registry

## Checks
- coverage: `workload_complete`, 8 waves, and 128 tiles
- conservation: delivered flits equal scheduled flits
- tag safety: collision-free 8-bit reuse is proven
- clock domains: compute releases are converted to absolute NoC cycles with
  `ceil(compute_cycles * compute_clock_ns / noc_clock_ns)`
- fast-forward: accelerated and unaccelerated simulations preserve absolute
  delivery cycles
- disclosure: all remaining storage, finalizer, and HBM abstractions are listed

## Local Commands
- `PYTHONPATH=control_plane python3 -m pytest -q control_plane/control_plane/tests/test_l2_task_generator.py -k score32_noc_phase2`
- `python3 -m pytest -q tests/test_noc_segmented_mesh.py tests/test_llm_decoder_attention_score32_noc_phase2_schedule.py`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed_for_dispatch
- note: Local contract and simulator tests passed; remote result checks remain pending.
