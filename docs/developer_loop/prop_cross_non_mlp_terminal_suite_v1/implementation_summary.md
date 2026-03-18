# Implementation Summary

## Proposal
- `proposal_id`: `prop_cross_non_mlp_terminal_suite_v1`
- `title`: `Terminal-sensitive softmax suite`

## Scope
- stage the first remote item as `measurement_only` on a small locally
  generated terminal-sensitive softmax-tail suite
- avoid pretending the repo already contains a broader non-MLP model set when
  the current mapper-supported ONNX subset is still `Cast/Gemm/Softmax`-centric
- defer the actual fused vs non-fused judgment to the second paired item

## Files Changed
- `docs/development_items/items/item_eval_non_mlp_terminal_suite_v1.md`
- `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1/proposal.json`
- `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1/design_brief.md`
- `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1/evaluation_gate.md`
- `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1/implementation_summary.md`
- `npu/mapper/examples/gen_softmax_classifier_suite_lite.py`
- `runs/models/onnx_terminal_softmax_suite_v1/README.md`
- `runs/models/onnx_terminal_softmax_suite_v1/manifest.json`
- `runs/models/onnx_terminal_softmax_suite_v1/softmax_cls_b128_i8_o16.onnx`
- `runs/models/onnx_terminal_softmax_suite_v1/softmax_cls_b256_i8_o64.onnx`
- `runs/models/onnx_terminal_softmax_suite_v1/softmax_cls_b128_i4_o128.onnx`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1/campaign.json`

## Local Validation
- `python3 -m py_compile npu/mapper/examples/gen_softmax_classifier_suite_lite.py`
- `python3 npu/mapper/examples/gen_softmax_classifier_suite_lite.py --out-dir runs/models/onnx_terminal_softmax_suite_v1`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1/campaign.json --check_paths`

## Evaluation Request
- measurement stage:
  - item: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1`
  - mode: `measurement_only`
  - merged evidence PR: `#49`
  - campaign:
    `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1/campaign.json`
- paired candidate stage:
  - item: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1`
  - mode: `paired_comparison`
  - merged evidence PR: `#52`
  - campaign:
    `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1/campaign.json`

## Risks
- locally generated softmax-tail graphs are a bounded generalization step, not
  the final non-MLP expansion target
- if the measurement-only stage shows no movement beyond the original proof, a
  broader suite may not be worth the next evaluation spend
