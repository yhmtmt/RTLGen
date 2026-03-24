# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_tanh_direct_output_v1`
- `title`: `Terminal tanh direct output`

## Scope
- add bounded terminal `Tanh` lowering to the mapper direct-output path
- generate a bounded tanh-first ONNX suite
- stage the evaluation as:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/onnx_to_schedule.py`
- `npu/mapper/run.py`
- `npu/mapper/examples/gen_terminal_tanh_suite_lite.py`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_tanh_suite_v1/manifest.json`
- `runs/models/onnx_terminal_tanh_suite_v1/*.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_tanh_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_tanh_suite_fused_nm1_v1/campaign.json`
- `docs/developer_loop/prop_l2_mapper_terminal_tanh_direct_output_v1/*`

## Local Validation
- `python3 tests/test_mapper_split.py`
- `python3 npu/mapper/examples/gen_terminal_tanh_suite_lite.py --out-dir runs/models/onnx_terminal_tanh_suite_v1`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_tanh_suite_submit_nm1_v1/campaign.json --check_paths`
- result: `pass`

## Remote Evaluation
- implementation commit: `bc283ad90bf21b0733312ada89cce61994883eb6`
- accepted baseline evidence:
  - PR `#82`
  - work item `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1`
  - run key `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1_run_8d7b68a4a8d31cd1`
- accepted aggregate baseline point:
  - `latency_ms_mean`: `0.007076666666666666`
  - `energy_mj_mean`: `2.533446666666667e-09`
  - `critical_path_ns_mean`: `2.8082`
  - `die_area_um2_mean`: `1440000.0`
  - `total_power_mw_mean`: `0.000358`

## Next Step
- queue the paired direct-output candidate:
  - `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1`
- do not promote the proposal until the paired result is reviewed against the merged baseline
