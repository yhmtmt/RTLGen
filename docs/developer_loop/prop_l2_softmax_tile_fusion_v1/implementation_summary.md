# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `title`: `Softmax-tail fused tile path`
- `status`: first implementation slice completed

## Scope
- Bounded implementation target:
  - reduce terminal softmax-tail overhead without broad scheduler redesign
  - make the behavior architecture-selected instead of hardwired
  - keep the change scoped to the imported softmax-tail workload family first
- In scope:
  - architecture config addition for a softmax-tail fused-output candidate
  - mapper lowering support for direct terminal softmax output
  - regression coverage for the fused-output lowering path
- Out of scope for the first implementation pass:
  - broad redesign of the generic NPU shell
  - non-softmax workload retuning
  - wide Layer 1 circuit search beyond the current selected SOFTMAX seed
  - changes to external/manual evaluation lane procedure

## Files Changed
- Implemented primary touch points:
  - `npu/mapper/onnx_to_schedule.py`
  - `npu/arch/examples/minimal_softmax_tail_fused.yml`
  - `npu/arch/schema_v0_2_draft.yml`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/objective_profiles.json`
  - `tests/test_mapper_split.py`
- Current implementation slice:
  - mapper now supports architecture-selected direct terminal softmax output
  - new example arch file enables that behavior for a bounded softmax-tail
    candidate
  - regression test proves the mapper emits `SOFTMAX -> Y_DRAM` directly and
    removes the trailing `dma_y`
- Still not implemented in this slice:
  - broader architecture or rtlgen generator changes
  - remote evaluation results for the new candidate
  - promotion artifacts for the new candidate

## Local Validation
- Completed local validation:
  - `python3 /workspaces/RTLGen/tests/test_mapper_split.py`
  - `python3 -m py_compile /workspaces/RTLGen/npu/mapper/onnx_to_schedule.py`
  - `python3 /workspaces/RTLGen/npu/arch/validate.py /workspaces/RTLGen/npu/arch/schema.yml /workspaces/RTLGen/npu/arch/examples/minimal_softmax_tail_fused.yml`
  - `python3 /workspaces/RTLGen/npu/eval/validate.py --campaign /workspaces/RTLGen/runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json --check_paths`
- Validation result:
  - mapper regression suite passed
  - new fused-output lowering regression passed
  - new architecture example passed schema validation
  - new fused-output campaign passed campaign validation
  - bounded routing-equivalence quality gate passed via
    `npu/eval/compare_terminal_softmax_quality.py`
- Pass/fail summary:
  - first implementation slice passed local validation
  - remote campaign validation still pending
  - remote PPA spend remains blocked only on human evaluation-gate approval

## Evaluation Request
- Requested remote tasks at the evaluation gate:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with `objective=balanced`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with `objective=latency`
- Cost class:
  - both are `high`
- Required comparison baselines:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- Required evidence:
  - campaign report
  - summary.csv
  - best_point.json
  - generated campaign file used for the run
- Evaluation should not be requested until:
  - evaluation gate is approved

## Risks
- Direct terminal output may improve only the descriptor tail overhead and not
  move the overall model ranking enough to justify a new default.
- The fused path may improve only the tiny softmax-tail classifier and not
  produce a defensible general architectural recommendation.
- Added area or descriptor complexity may erase any latency gain.
- The current best integrated SOFTMAX baseline may already capture most of the
  practical benefit, leaving little room for a new architecture point.
