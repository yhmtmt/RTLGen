# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_memory_aware_split_v1`
- `candidate_id`: `cand_l2_mapper_memory_aware_split_v1_r1`

## Evaluations Consumed
- work item id: `l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2`
- run key: `l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2_run_1814edb5310cb2e8`
- source commit: `68857fd1c017c9025d20c12607e29e8733cfd580`
- merged evidence PR: `#44`

## Baseline Comparison
- baseline used: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355/`
- `fp16_nm2_softmax_r4 / flat_nomacro`
  - latency: `0.000928 ms -> 0.000621 ms`
  - energy: `1.7546067199999999e-07 mJ -> 1.17414954e-07 mJ`
- `fp16_nm2_softmax_r4 / hier_macro`
  - latency: `0.000928 ms -> 0.000621 ms`
  - energy: `1.8455878400000002e-07 mJ -> 1.23503238e-07 mJ`
- committed focused evidence now includes the emitted `schedule.yml` and `trace.json`, and the schedule shows monolithic terminal GEMM execution with `m: 256` and no row split.

## Result
- result: win
- confidence level: medium-high
- estimated mapper optimization room: reduced for this benchmark family after the bounded final-stage policy; broader mapper search is still open for other workloads
- architecture conclusion robustness: the earlier `nm2` loss on this benchmark was not robust to plausible schedule changes; it was mapper-confounded

## Failures and Caveats
- no flow or validation failures in the accepted rerun
- this proof is intentionally narrow: it validates the bounded terminal-softmax row-split policy on the focused `nm2` softmax-tail benchmark only
- the mapper notes in `schedule.yml` still retain some generic chunk metadata, so future cleanup should keep the descriptive notes aligned with the final emitted monolithic schedule
- this result does not yet answer the broader `nm1` vs `nm2` architecture ranking question under wider workloads

## Recommendation
- promote
- short reason: the bounded mapper policy materially improved `nm2` on the intended focused proof and the emitted schedule evidence confirms the intended monolithic final-stage lowering
- follow-on: use this mapper policy as the new evaluation baseline for future multi-module softmax-tail studies, then open a separate broader reintegration evaluation if you want to revisit cross-architecture ranking
