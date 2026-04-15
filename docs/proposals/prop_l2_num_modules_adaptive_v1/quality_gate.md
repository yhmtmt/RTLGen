# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_num_modules_adaptive_v1`
- `title`: `Adaptive num_modules selection for imported softmax-tail workloads`

## Why This Gate Is Required
- The proposal is architecture-level, but the refreshed conclusion still relies
  on imported softmax-tail correctness and comparable model-level outputs across
  `nm1` and `nm2`.
- We need the rerun to preserve the existing model-quality contract while we
  reassess latency and energy under the newer mapper baseline.

## Reference
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1`
- reference_ref: `runs/models/onnx_imported_softmax_tail_v1/manifest.json`

## Checks
- metric:
  - threshold: matched `status=ok` campaign rows for both `fp16_nm1` and `fp16_nm2`
- metric:
  - threshold: no regression in existing model-quality checks relative to the campaign baseline

## Local Commands
- command: `python3 -m control_plane.cli.main generate-l2-campaign ...`

## Result
- status: pending
- note: Evaluate after the refreshed `num_modules` campaign is available.
