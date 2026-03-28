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
  - the paired direct-output candidate stays on the same bounded suite and resolves the merged baseline correctly

## Reference
- baseline_ref: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1` / PR `#75`
- paired_ref: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1` / PR `#76`
- physical_ref: accepted reduced integrated sigmoid proxy `npu_fp16_cpp_nm1_sigmoidproxy`

## Checks
- non-fused and direct-output schedules stay within bounded terminal sigmoid legality
- the paired candidate compares only against the merged/materialized baseline on the same three-model suite
- the paired candidate improves latency and energy without regressing the shared physical source metrics

## Local Commands
- `python3 tests/test_mapper_split.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_activation_family_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_activation_family_suite_fused_nm1_v1/campaign.json --check_paths`

## Result
- status: accepted_for_bounded_sigmoid_scope
- note: the bounded sigmoid-first suite now has accepted baseline and paired direct-output evidence; broader nonlinear-family quality hooks remain follow-on work
