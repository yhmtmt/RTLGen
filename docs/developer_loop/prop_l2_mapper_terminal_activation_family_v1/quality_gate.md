# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `title`: `Terminal activation-family direct output`

## Why This Gate Is Required
- the first bounded nonlinear family extends the accepted terminal vec-op path beyond `Relu`
- these ops are more numerically sensitive than the accepted standalone `Relu` vec-op path
- remote paired-comparison evaluation should not proceed until:
  - accepted lower-layer sigmoid physical sources exist
  - the non-fused Layer 2 baseline is merged
  - local output-quality checks for direct-output `Sigmoid` are defined

## Reference
- baseline_ref: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1` / PR `#75`
- reference_ref: accepted reduced integrated sigmoid proxy `npu_fp16_cpp_nm1_sigmoidproxy`

## Checks
- confirm non-fused and direct-output schedules preserve bounded terminal sigmoid legality
- define a local output-quality comparison for the paired direct-output candidate
- keep the paired candidate on the same three-model bounded suite as the accepted baseline

## Local Commands
- pending paired direct-output implementation

## Result
- status: pending_paired_candidate
- note: lower-layer prerequisites and the measurement baseline are accepted; the remaining gate is the direct-output paired candidate quality check
