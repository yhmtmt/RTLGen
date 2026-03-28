# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_mapper_memory_aware_split_v1`
- `title`: `Memory-aware split policy for multi-module softmax-tail mapping`

## Why This Gate Is Required
- This proposal changes the schedule shape of the terminal GEMM that feeds the
  dedicated terminal softmax on multi-module hardware.
- The intended behavior is semantic preservation: the same GEMM and softmax
  math, but without forcing row-splitting when the split is likely to be pure
  control overhead.
- Before remote evaluation spend, the local gate should confirm that the
  emitted schedule remains valid for the targeted classifier shape and that the
  direct-output softmax path is preserved.

## Reference
- baseline_ref:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/`
- reference_ref:
  - dedicated-softmax mapper regressions in `tests/test_mapper_split.py`
  - campaign-note regression in `tests/test_run_campaign_mapper_notes.py`

## Checks
- schedule structure for tiny terminal-softmax classifiers
  - threshold: terminal final GEMM stays legal and becomes monolithic for the
    targeted tiny multi-module case
- terminal softmax routing behavior
  - threshold: direct-output softmax path remains intact when the architecture
    requests it, with no trailing `dma_y`
- mapper metadata/reporting alignment
  - threshold: campaign mapper notes report the final linear split decision
    rather than stale generic row-split metadata

## Local Commands
- `python3 -m py_compile /workspaces/RTLGen/npu/mapper/onnx_to_schedule.py /workspaces/RTLGen/npu/eval/run_campaign.py`
- `python3 /workspaces/RTLGen/tests/test_mapper_split.py`
- `python3 /workspaces/RTLGen/tests/test_run_campaign_mapper_notes.py`

## Result
- status: passed
- validated_utc: `2026-03-17T07:00:00Z`
- note: The bounded local gate passed. The targeted dedicated-softmax classifier
  schedules now keep the final GEMM monolithic on the tiny multi-module case,
  preserve terminal softmax direct-output behavior, and emit stage-specific
  mapper metadata that downstream campaign notes consume correctly.
