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
- do not queue the paired-comparison stage yet

## Files Changed
- `npu/mapper/onnx_lite.py`
- `npu/mapper/examples/gen_terminal_direct_output_suite_lite.py`
- `tests/test_mapper_split.py`
- `runs/models/onnx_terminal_direct_output_suite_v1/README.md`
- `runs/models/onnx_terminal_direct_output_suite_v1/manifest.json`
- `runs/models/onnx_terminal_direct_output_suite_v1/*.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json`
- `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1/proposal.json`
- `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1/design_brief.md`
- `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1/evaluation_gate.md`
- `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1/evaluation_requests.json`

## Local Validation
- `python3 npu/mapper/examples/gen_terminal_direct_output_suite_lite.py --out-dir runs/models/onnx_terminal_direct_output_suite_v1`
- `python3 tests/test_mapper_split.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json --check_paths`
- `python3 -m py_compile npu/mapper/onnx_lite.py npu/mapper/examples/gen_terminal_direct_output_suite_lite.py`
- result:
  - pass
  - the terminal `Relu` model is accepted by the current mapper as a legal
    measurement baseline, but it still lowers to a non-fused final `dma_y1`
    tail rather than a direct-output writeback

## Evaluation Request
- first remote stage should use:
  - campaign: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1/campaign.json`
  - mode: `measurement_only`
  - objective: `terminal_op_reference_metrics`
  - item_id: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- first-stage purpose:
  - record plain `fp16_nm1` non-fused reference metrics for terminal linear and
    terminal `Relu` before any mapper direct-output change is implemented
- paired comparison is intentionally deferred until the direct-output lowering
  rule for the selected family exists locally
- queue status:
  - not queued yet
  - local queue insertion failed because the local control-plane PostgreSQL
    endpoint at `localhost:5432` was unavailable during this session

## Risks
- terminal linear plus terminal `Relu` is a bounded but still close neighbor to
  the accepted softmax-tail proof
- terminal `Relu` may still need a quality gate once direct-output lowering is
  introduced
- broader terminal-op families remain out of scope for this first pass
