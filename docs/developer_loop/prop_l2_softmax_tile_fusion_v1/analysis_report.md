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
- result: `flat`
- confidence: `medium`
- estimated mapper optimization room: `low for the direct nm1 comparison`
- architecture conclusion robust to plausible schedule changes: `not fully`
- interpretation:
  - the fused terminal-output path is legal and preserved the expected
    architecture/mechanism change
  - the focused `nm1` evaluation did not show measurable improvement over the
    accepted non-fused softmax baseline
  - the expected skipped intermediate memory access is therefore not on the
    measured critical path for this benchmark as currently evaluated

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
- further evaluation should focus on proving or disproving those explanations,
  not on relitigating the already-complete legality result

## Recommendation
- `iterate`
- reason:
  the evidence is valid and merge-worthy, but it does not prove a measurable
  fused-output benefit on the focused `nm1` baseline
- follow-on:
  stay in the same proposal only if the next step is a bounded proof-oriented
  evaluation of the fused mechanism on a more stress-relevant workload or
  trace-based analysis of why the skipped memory hop is hidden; otherwise open a
  new intake item for perf-model or benchmark-sensitivity work
