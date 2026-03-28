# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_mapper_terminal_op_generalization_v1`
- `title`: `Generalized terminal-op direct output`

## Scope
- define the first bounded terminal-op family as terminal linear plus terminal
  `Relu` on fixed `fp16_nm1`
- add a local ONNX-lite generator and a measurement-only campaign scaffold for
  that suite
- confirm the current mapper can lower terminal `Relu` graphs as non-fused
  baselines before any direct-output generalization is attempted
- implement the bounded direct-output lowering for the same family and queue a
  paired comparison against the merged measurement baseline

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/examples/gen_terminal_direct_output_suite_lite.py`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_direct_output_suite_v1/README.md`
- `runs/models/onnx_terminal_direct_output_suite_v1/manifest.json`
- `runs/models/onnx_terminal_direct_output_suite_v1/*.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_fused_nm1_v1/campaign.json`
- `npu/arch/examples/minimal_terminal_direct_output.yml`
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/proposal.json`
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/design_brief.md`
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/evaluation_gate.md`
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/evaluation_requests.json`

## Local Validation
- `python3 npu/mapper/examples/gen_terminal_direct_output_suite_lite.py --out-dir runs/models/onnx_terminal_direct_output_suite_v1`
- `python3 tests/test_mapper_split.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_fused_nm1_v1/campaign.json --check_paths`
- `python3 -m py_compile npu/mapper/onnx_lite.py npu/mapper/examples/gen_terminal_direct_output_suite_lite.py`
- result:
  - pass
  - terminal `Relu` is now preserved as a final GEMM epilogue instead of being
    dropped on the last stage
  - the bounded direct-output arch constraint now writes terminal linear and
    terminal `Relu` outputs directly to `Y_DRAM`, removing the final `dma_y*`
    tail on the candidate path

## Evaluation Request
- first remote stage should use:
  - campaign: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json`
  - mode: `measurement_only`
  - objective: `terminal_op_reference_metrics`
  - item_id: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- first-stage purpose:
  - record plain `fp16_nm1` non-fused reference metrics for terminal linear and
    terminal `Relu` before any mapper direct-output change is implemented
- second remote stage should use:
  - campaign: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_fused_nm1_v1/campaign.json`
  - mode: `paired_comparison`
  - objective: `terminal_op_direct_output_vs_nonfused`
  - baseline item: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- second-stage purpose:
  - compare bounded direct-output lowering against the merged non-fused
    measurement baseline on the same terminal linear plus terminal `Relu` suite
- queue status:
  - first stage merged via PR `#54`
  - second stage pending queue insertion after this implementation commit is
    pushed

## Risks
- terminal linear plus terminal `Relu` is a bounded but still close neighbor to
  the accepted softmax-tail proof
- terminal `Relu` may still need a quality gate once direct-output lowering is
  introduced
- broader terminal-op families remain out of scope for this first pass
