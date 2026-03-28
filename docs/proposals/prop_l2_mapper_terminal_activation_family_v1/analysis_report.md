# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `candidate_id`: `cand_l2_mapper_terminal_activation_family_v1_r1`

## Evaluations Consumed
- accepted lower-layer prerequisites:
  - standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1` / PR `#63`
  - integrated sigmoid-enabled `nm1` architecture-block source from `prop_l1_npu_nm1_sigmoid_vec_enable_v1` / PR `#74`
- accepted Layer 2 measurement baseline:
  - work item: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
  - run key: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1_run_8b59dfa21c40c9c5`
  - merged evidence PR: `#75`
  - source commit under test: `b3c45a2842671dafa41730d15b840aff69c538b2`
- accepted Layer 2 paired direct-output comparison:
  - work item: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1`
  - run key: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1_run_094dcc51a8e51d63`
  - merged evidence PR: `#76`
  - source commit under test: `91724473c5a6c1f697a3d36ca9c1d353f9871816`

## Baseline Comparison
- the activation-family mapper work is no longer blocked on lower-layer physical grounding
- the accepted integrated source remains the reduced proxy `npu_fp16_cpp_nm1_sigmoidproxy`, which is sufficient to ground this bounded Layer 2 staged proof
- the bounded first-pass sigmoid suite has accepted paired evidence for:
  - `sigmoid_vec_b128_f64`
  - `sigmoid_vec_b256_f256`
  - `sigmoid_vec_flatten_b128_2x4x8`
- aggregate accepted means on `fp16_nm1_sigmoidproxy` / `hier_macro`:
  - non-fused latency: `0.007076666666666666 ms`
  - fused latency: `0.0052699999999999995 ms`
  - non-fused energy: `2.5476e-09 mJ`
  - fused energy: `1.8972e-09 mJ`
  - critical path: `2.7883 ns` unchanged
  - die area: `1440000.0 um^2` unchanged
  - total power: `0.00036 mW` unchanged
- the paired direct-output candidate improves latency and energy on all four matched rows without regressing the shared physical source metrics

## Result
- result: `paired_win_accepted`
- confidence level: `medium`
- estimated mapper optimization room: `validated for the bounded sigmoid-first family on fixed nm1`
- architecture conclusion robustness: `sufficient for bounded staged promotion, but still grounded by the reduced sigmoid proxy rather than full npu_top`

## Failures and Caveats
- the accepted integrated physical source is a reduced `architecture_block` proxy rather than full `npu_top`
- that is sufficient for this staged bounded Layer 2 proof, but it should not be overstated as a full-top architecture ranking result
- the first bounded nonlinear family is still only `Sigmoid`; broader activation-family claims remain open
- stronger quality and legality hooks may still be required before extending beyond this bounded sigmoid-first scope

## Recommendation
- `promote`
- short reason:
  merged PR `#75` established the bounded sigmoid-first non-fused baseline and merged PR `#76` showed direct terminal sigmoid vec-op output improving latency and energy across the whole matched suite on fixed `nm1`
- follow-on:
  broaden mapper or lowering support to the next bounded nonlinear activation family only after preserving the same dependency-ordered staged evaluation model
