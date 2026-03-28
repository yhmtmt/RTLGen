# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `candidate_id`: `cand_softmax_tail_fused_output_nm1_focus_r2`

## Evaluations Consumed
- work item id: `l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2`
- run key: `l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2_run_392da4f54afe565a`
- source commit: `7b63d4207d6353d773a3c322b87b7710d8e88f3d`
- merged review PR: `#41`

## Baseline Comparison
- baseline:
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- direct comparison:
  `fp16_nm1_softmax_r4` non-fused baseline vs
  `fp16_nm1_softmax_r4` fused candidate
- key deltas:
  - `flat_nomacro`: latency `0.000621 -> 0.000621 ms`, energy
    `1.1462914800000001e-07 -> 1.1462914800000001e-07 mJ`
  - `hier_macro`: latency `0.000621 -> 0.000621 ms`, energy
    `1.2585186e-07 -> 1.2585186e-07 mJ`
  - no measurable aggregate or per-model delta was observed in the committed
    campaign outputs

## Result
- result: `superseded`
- confidence: `medium`
- estimated mapper optimization room: `captured by later follow-on proposals`
- architecture conclusion robust to plausible schedule changes: `not pursued further in this proposal`
- interpretation:
  - the fused terminal-output path is legal and preserved the expected
    architecture/mechanism change
  - the focused `nm1` evaluation did not show measurable improvement over the
    accepted non-fused softmax baseline
  - the expected skipped intermediate memory access is therefore not on the
    measured critical path for this benchmark as currently evaluated
  - the follow-on question was later handled by the overlap-probe and newer
    bounded direct-output proposal family, so this proposal no longer needs to
    stay open in `iterate`

## Failures and Caveats
- no remote flow failures were reported
- no quality-gate regression was reported
- likely reasons the expected gain did not appear:
  - the benchmark is too small and tail-light for the removed terminal memory
    access to dominate total latency
  - the current execution/perf path may already overlap much of the terminal
    transfer cost
  - the current model family may not stress the fused-output mechanism strongly
    enough to prove its benefit
- further evaluation was superseded by newer proposals instead of continuing in
  this proposal thread

## Recommendation
- `superseded`
- reason:
  the evidence is valid historical input, but the unresolved mechanism question
  has been superseded by newer proposals that already carried the follow-on work
- follow-on:
  no further work should be queued under this proposal; use the newer overlap
  and bounded direct-output proposals as the canonical continuation
