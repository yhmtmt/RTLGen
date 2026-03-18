# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- `candidate_id`: `cand_l2_mapper_terminal_vecop_direct_output_v1_r1`

## Evaluations Consumed
- measurement baseline work item:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`
- measurement baseline run key:
  `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2_run_eacb4da28b6e09ba`
- source commit:
  `37d18aae5dba13086d7b15ac57381e6fa719f40f`
- merged evidence PR:
  `#58`

## Baseline Comparison
- measurement-only reference stage only; no proposal judgment emitted yet
- accepted baseline evidence:
  `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2/`
- bounded suite covered:
  - `relu_vec_b128_f64`
  - `relu_vec_b256_f256`
  - `relu_vec_flatten_b128_2x4x8`
- representative accepted `flat_nomacro` reference metrics:
  - aggregate latency mean: `0.007076666666666666 ms`
  - aggregate energy mean: `1.36666002e-06 mJ`

## Result
- result: `measurement_baseline_accepted`
- confidence level:
  `high for the bounded standalone terminal Relu suite on fixed nm1 as a clean reference point`
- estimated mapper optimization room:
  `unknown for the direct-output hypothesis because the paired comparison has not run yet`
- architecture conclusion robustness:
  `not yet applicable; this stage only establishes the non-fused baseline`

## Failures and Caveats
- PR `#57` was superseded because it mixed the valid measurement payload with
  unrelated notebook-side history; PR `#58` is the accepted clean evidence
  boundary
- this accepted result says nothing yet about direct-output benefit; it only
  proves that the bounded standalone terminal Relu suite is measurable,
  reviewable, and exported cleanly under `measurement_only`
- the current conclusion is intentionally limited to fixed `fp16_nm1`

## Recommendation
- `iterate`
- short reason:
  the accepted measurement stage successfully establishes the non-fused nm1
  baseline for the bounded standalone terminal Relu suite, so the proposal
  should advance to its paired direct-output comparison rather than stop here
- follow-on:
  queue and review the paired `direct_output vs non_fused` item on the same
  suite, then decide promote or reject from that focused comparison
