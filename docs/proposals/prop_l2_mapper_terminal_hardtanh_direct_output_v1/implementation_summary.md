# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_hardtanh_direct_output_v1`
- `title`: `Terminal hardtanh direct output`

## Scope
- add bounded terminal `HardTanh` lowering to the mapper direct-output path
- generate a bounded HardTanh-first ONNX suite
- stage the evaluation as:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/onnx_to_schedule.py`
- `npu/mapper/run.py`
- `npu/mapper/examples/gen_terminal_hardtanh_suite_lite.py`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_hardtanh_suite_v1/*`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1/campaign.json`
- `docs/proposals/prop_l2_mapper_terminal_hardtanh_direct_output_v1/*`

## Local Validation
- `python3 -m py_compile npu/mapper/onnx_lite.py npu/mapper/onnx_to_schedule.py npu/mapper/run.py npu/mapper/examples/gen_terminal_hardtanh_suite_lite.py tests/test_mapper_split.py`
- `python3 tests/test_mapper_split.py`
- `python3 npu/mapper/examples/gen_terminal_hardtanh_suite_lite.py --out-dir runs/models/onnx_terminal_hardtanh_suite_v1`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1/campaign.json --check_paths`
- result: `pass`

## Remote Evaluation
- queued baseline item:
  - `l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_measurement_r1`
