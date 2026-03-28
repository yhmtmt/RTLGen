# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- `title`: `Terminal vec-op direct output`

## Scope
- bounded first-pass family defined as standalone terminal `Relu`
- mapper now lowers standalone terminal `Relu` graphs to `vec_op`
- direct terminal vec-op output is locally supported behind a dedicated arch
  constraint, and the proposal has already cleared its `measurement_only`
  baseline stage
- the next remote step is the paired direct-output comparison on the same
  bounded suite

## Files Changed
- `docs/backlog/items/item_l2_mapper_terminal_vecop_direct_output_v1.md`
- `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/proposal.json`
- `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/design_brief.md`
- `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/evaluation_gate.md`
- `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/implementation_summary.md`
- `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1/evaluation_requests.json`
- `npu/mapper/onnx_lite.py`
- `npu/mapper/onnx_to_schedule.py`
- `npu/mapper/examples/gen_terminal_vecop_suite_lite.py`
- `npu/arch/examples/minimal_terminal_vecop_direct_output.yml`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_vecop_suite_v1/README.md`
- `runs/models/onnx_terminal_vecop_suite_v1/manifest.json`
- `runs/models/onnx_terminal_vecop_suite_v1/relu_vec_b128_f64.onnx`
- `runs/models/onnx_terminal_vecop_suite_v1/relu_vec_b256_f256.onnx`
- `runs/models/onnx_terminal_vecop_suite_v1/relu_vec_flatten_b128_2x4x8.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_fused_nm1_v1/campaign.json`

## Local Validation
- `python3 npu/mapper/examples/gen_terminal_vecop_suite_lite.py --out-dir runs/models/onnx_terminal_vecop_suite_v1`
- `python3 tests/test_mapper_split.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_fused_nm1_v1/campaign.json --check_paths`
- `python3 -m py_compile npu/mapper/onnx_lite.py npu/mapper/onnx_to_schedule.py npu/mapper/examples/gen_terminal_vecop_suite_lite.py`
- result:
  - local lowering is legal for standalone terminal `Relu`
  - local direct-output emission is legal behind the dedicated vec-op arch flag
  - both the accepted measurement campaign and the paired fused campaign are
    path-valid

## Evaluation Request
- accepted measurement evidence:
  - PR `#58`
  - work item:
    `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`
- next local step:
  - queue the paired `direct_output vs non_fused` item for the same
    standalone terminal `Relu` suite
  - require committed schedule and perf evidence for all suite models because
    the suite is small and model identity matters to the proof

## Risks
- the bounded `Relu` family may be too narrow to justify a later broader claim
- direct-output for standalone vec-op tails may still expose a separate perf
  or review-evidence issue once the paired stage starts
- the next bottleneck after measurement may be export/review structure rather
  than mapper legality
