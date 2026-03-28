# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_hardsigmoid_direct_output_v1`
- `title`: `Terminal hard-sigmoid direct output`

## Scope
- add bounded terminal `HardSigmoid` lowering to the mapper direct-output path
- generate a bounded hard-sigmoid-first ONNX suite
- stage the evaluation as:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/onnx_to_schedule.py`
- `npu/mapper/run.py`
- `npu/mapper/examples/gen_terminal_hardsigmoid_suite_lite.py`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_hardsigmoid_suite_v1/manifest.json`
- `runs/models/onnx_terminal_hardsigmoid_suite_v1/*.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_hardsigmoid_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_hardsigmoid_suite_fused_nm1_v1/campaign.json`
- `docs/proposals/prop_l2_mapper_terminal_hardsigmoid_direct_output_v1/*`

## Local Validation
- `python3 -m py_compile npu/mapper/onnx_lite.py npu/mapper/onnx_to_schedule.py npu/mapper/run.py npu/mapper/examples/gen_terminal_hardsigmoid_suite_lite.py tests/test_mapper_split.py`
- `python3 tests/test_mapper_split.py`
- `python3 npu/mapper/examples/gen_terminal_hardsigmoid_suite_lite.py --out-dir runs/models/onnx_terminal_hardsigmoid_suite_v1`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_hardsigmoid_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_hardsigmoid_suite_fused_nm1_v1/campaign.json --check_paths`
- result: `pass`

## Remote Evaluation
- not queued yet
