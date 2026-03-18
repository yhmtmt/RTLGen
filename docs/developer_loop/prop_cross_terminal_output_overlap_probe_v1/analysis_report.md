# Analysis Report

## Candidate
- `proposal_id`: `prop_cross_terminal_output_overlap_probe_v1`
- `candidate_id`: `cand_terminal_output_overlap_probe_nm1_fused_r1`

## Evaluations Consumed
- refreshed baseline work item: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r1`
- refreshed baseline run key:
  `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r1_run_dfc22867015d55ad`
- paired candidate work item: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1`
- paired candidate run key:
  `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1_run_0753b5782827c85e`
- source commit:
  `af5013f80951926308fa9aeadbf59723a3e2553a`
- merged evidence PRs:
  - refreshed baseline: `#47`
  - paired candidate: `#48`

## Baseline Comparison
- historical baseline used for rebaseline context:
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- corrected-contract direct comparison used for proposal judgment:
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_nm1_v2__l2_prop_cross_terminal_output_overlap_probe_v1_nm1_baseline_r1/`
  vs
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_nm1_v2__l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1/`
- key deltas:
  - contract correction rebaseline:
    - `flat_nomacro`: latency `0.000621 -> 0.00096775 ms`, energy
      `1.1462914800000001e-07 -> 1.78635037e-07 mJ`
    - `hier_macro`: latency `0.000621 -> 0.00096775 ms`, energy
      `1.2585186e-07 -> 1.96124215e-07 mJ`
  - corrected-contract fused benefit:
    - `flat_nomacro`: latency `0.00096775 -> 0.0008037500000000001 ms`,
      energy `1.78635037e-07 -> 1.48362605e-07 mJ`
    - `hier_macro`: latency `0.00096775 -> 0.0008037500000000001 ms`,
      energy `1.96124215e-07 -> 1.6288797499999998e-07 mJ`
- interpretation:
  - the old immediate-event model hid part of the terminal `dma_y` cost
  - once perf and shell semantics were aligned to completion-bound events, the
    expected fused-output benefit became measurable on the focused `nm1` proof

## Result
- result: `win`
- confidence level: `high for the focused mechanism question`
- estimated mapper optimization room: `low for this fixed-architecture paired proof`
- architecture conclusion robustness:
  `robust for the corrected-contract nm1 direct comparison; the earlier flat result was not robust because it depended on incorrect event semantics`

## Failures and Caveats
- no flow or validation failures in the accepted reruns
- this proposal answered a mechanism-level question, not a broad architecture
  ranking question
- the accepted result is intentionally narrow:
  - one fixed `nm1` architecture
  - one model family
  - corrected event contract only
- broader `nm1`/`nm2` ranking or workload-general claims still require separate
  follow-on evaluation
- historical reports produced under the old immediate-event contract should not
  be treated as authoritative for terminal-output mechanism questions

## Recommendation
- `promote`
- short reason:
  the accepted reruns prove that fused terminal output improves latency and
  energy once the perf and shell event semantics are corrected to enforce real
  producer-completion dependencies
- follow-on:
  adopt the corrected event contract as the evaluation baseline for future
  terminal-output studies and only open a broader reintegration evaluation if
  you want to revisit wider workload or cross-architecture ranking
