## Summary
- item_id: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1_run_baa0b349b4e529b5`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_op_generalization_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_op_generalization_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `Direct terminal-output lowering should remove the final dma_y tail on at least part of the bounded terminal linear plus terminal Relu suite.`
- expectation_status: `as_expected`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `Can a bounded mapper program for terminal linear and terminal Relu outputs establish clean nm1 reference points first, before direct-output generalization is attempted on those same points?`
- comparison_role: `candidate`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- baseline_item_id: `l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1`
- latency_delta fp16_nm1/flat_nomacro/linear_tail_b128_f8_o64: `0.002278` -> `0.001666` ms
- energy_delta fp16_nm1/flat_nomacro/linear_tail_b128_f8_o64: `4.39931916e-07` -> `3.21741252e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/linear_tail_b256_f8_o128: `0.0071779999999999995` -> `0.00503` ms
- energy_delta fp16_nm1/flat_nomacro/linear_tail_b256_f8_o128: `1.386229716e-06` -> `9.7140366e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/relu_tail_b128_f8_o128: `0.003914` -> `0.0027900000000000004` ms
- energy_delta fp16_nm1/flat_nomacro/relu_tail_b128_f8_o128: `7.55879508e-07` -> `5.3881038e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
