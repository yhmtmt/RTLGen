# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_memory_aware_split_v1`
- `title`: `Memory-aware split policy for multi-module softmax-tail mapping`
- `status`: first implementation slice completed

## Scope
- Bounded implementation target:
  - keep the existing `softmaxcmp` hardware fixed
  - update mapper lowering only for the terminal linear stage that feeds a
    dedicated terminal softmax
  - avoid row-splitting tiny final GEMMs when the split is likely to add
    synchronization overhead without reducing the serial softmax tail enough
- In scope:
  - new final-stage row-chunk chooser in the generic supported-graph mapper
  - stage-specific mapper metadata for the final linear row decision
  - campaign-note extraction aligned to the final linear split decision
  - regression coverage for tiny softmax-tail classifiers using the dedicated
    softmax backend
- Out of scope for this first mapper pass:
  - hardware or RTL changes
  - broad search-based mapper redesign
  - changes to the fallback MLP schedule builder
  - changes to campaign definitions or physical design points

## Files Changed
- `npu/mapper/onnx_to_schedule.py`
- `npu/eval/run_campaign.py`
- `tests/test_mapper_split.py`
- `tests/test_run_campaign_mapper_notes.py`

Current implementation slice:
- the generic mapper now chooses monolithic execution for the terminal GEMM
  when `gemm_num_modules > 1` but the per-module work estimate would be too
  small to justify row-splitting
- the first heuristic threshold is `8192` per-module MACs, applied only to the
  terminal-softmax stage
- emitted mapper notes now record `final_linear_row_parallel_enabled` and
  `final_linear_row_chunks`
- campaign summary notes now prefer the final-stage metadata so downstream
  review reflects the actual decision under test

## Local Validation
- Commands run:
  - `python3 -m py_compile /workspaces/RTLGen/npu/mapper/onnx_to_schedule.py /workspaces/RTLGen/npu/eval/run_campaign.py`
  - `python3 /workspaces/RTLGen/tests/test_mapper_split.py`
  - `python3 /workspaces/RTLGen/tests/test_run_campaign_mapper_notes.py`
- Result:
  - pass
  - `tests/test_mapper_split.py`: `Ran 7 tests ... OK`
  - `tests/test_run_campaign_mapper_notes.py`: `Ran 6 tests ... OK`

## Evaluation Request
- Requested remote tasks at the evaluation gate:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with `objective=balanced`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with `objective=latency`
- Cost class:
  - both are `medium`
- Required comparison baselines:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/`
- Required evidence:
  - campaign report
  - `summary.csv`
  - `best_point.json`
  - generated campaign file used for the run
  - emitted schedules for `fp16_nm1_softmax_r4` and `fp16_nm2_softmax_r4`

## Risks
- The current heuristic is intentionally narrow and may be too conservative or
  too specific to the tiny softmax-tail benchmark.
- The generic supported-graph path is updated, but the older fallback MLP path
  is unchanged and could still hide similar issues in another benchmark family.
- Even with a better final-stage split policy, `nm2` may still lose if lower
  Fmax and the unchanged serial softmax tail dominate.
- A fairer result on this benchmark does not yet imply the mapper has enough
  search breadth for more complex architectures.
