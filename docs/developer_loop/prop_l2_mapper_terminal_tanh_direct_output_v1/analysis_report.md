# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_tanh_direct_output_v1`
- `candidate_id`: baseline accepted, paired comparison pending

## Evaluations Consumed
- accepted lower-layer prerequisites:
  - standalone tanh wrapper from `prop_l1_terminal_tanh_block_v1`
  - integrated `nm1_tanhproxy` architecture-block source from `prop_l1_npu_nm1_tanh_vec_enable_v1`
- accepted Layer 2 measurement baseline:
  - work item: `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1`
  - run key: `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1_run_8d7b68a4a8d31cd1`
  - merged evidence PR: `#82`

## Baseline Summary
- bounded tanh-first non-fused baseline is now accepted on fixed `nm1`
- recommendation payload selected:
  - `arch_id`: `fp16_nm1_tanhproxy`
  - `latency_ms_mean`: `0.007076666666666666`
  - `energy_mj_mean`: `2.533446666666667e-09`
  - `critical_path_ns_mean`: `2.8082`
  - `die_area_um2_mean`: `1440000.0`
  - `total_power_mw_mean`: `0.000358`
- model coverage:
  - `tanh_vec_b128_f64`
  - `tanh_vec_b256_f256`
  - `tanh_vec_flatten_b128_2x4x8`

## Result
- result: `baseline_accepted`
- confidence level: `medium`
- architecture conclusion robustness: `not yet evaluable without the paired direct-output comparison`

## Failures and Caveats
- this accepted evidence is still the non-fused baseline only; it does not answer the direct-output hypothesis yet
- the accepted physical grounding remains the reduced `npu_fp16_cpp_nm1_tanhproxy` architecture-block source rather than full `npu_top`
- no correctness or review-payload issues remain in the merged baseline PR

## Recommendation
- `iterate`
- short reason:
  the bounded tanh baseline is now accepted and mergeable evidence, but the proposal question is only answered after the dependency-gated fused direct-output comparison runs against this merged baseline
- next action:
  queue `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1`
