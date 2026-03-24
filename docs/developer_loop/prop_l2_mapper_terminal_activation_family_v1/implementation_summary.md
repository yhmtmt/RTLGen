# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_activation_family_v1`
- `title`: `Terminal activation-family direct output`

## Scope
- first bounded sigmoid-first Layer 2 baseline is implemented and accepted
- standalone and integrated sigmoid lower-layer prerequisites are accepted and merged
- current implementation scope:
  - terminal `Sigmoid` mapper lowering through the existing terminal vec-op path
  - bounded ONNX suite generation for three small sigmoid terminal cases
  - measurement-only `nm1` campaign wired to the accepted reduced sigmoid proxy
- current missing step:
  - paired direct-output campaign implementation on the same suite

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/onnx_to_schedule.py`
- `npu/mapper/run.py`
- `npu/mapper/examples/gen_terminal_activation_family_suite_lite.py`
- `runs/models/onnx_terminal_activation_family_suite_v1/*`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_activation_family_suite_submit_nm1_v1/campaign.json`
- `tests/test_mapper_split.py`
- `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/implementation_summary.md`

## Local Validation
- `python3 tests/test_mapper_split.py`
- `python3 npu/mapper/examples/gen_terminal_activation_family_suite_lite.py --out-dir runs/models/onnx_terminal_activation_family_suite_v1`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_activation_family_suite_submit_nm1_v1/campaign.json --check_paths`

## Evaluation Request
- accepted baseline:
  - `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
  - merged evidence PR: `#75`
- next local step:
  - implement the paired direct-output campaign for the same sigmoid-first suite
  - then queue `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1`

## Risks
- the first bounded family is still only `Sigmoid`, not a broader nonlinear set
- direct-output quality tolerance for nonlinear activations remains unproven until the paired comparison stage
- the reduced sigmoid proxy is a lower-layer physical grounding source, not a full-top physical point
