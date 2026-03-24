## Summary
- item_id: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1_run_094dcc51a8e51d63`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_activation_family_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_activation_family_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- abstraction_layer: `full_architecture`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `Direct terminal sigmoid vec-op output should reduce the final writeback tail on at least part of the bounded sigmoid-first suite against the accepted non-fused baseline.`
- expectation_status: `as_expected`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `Can a bounded nonlinear terminal activation family establish clean nm1 reference points first, then show a direct-output win on those same points without reopening broader ranking?`
- comparison_role: `candidate`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_terminal_activation_family_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
- baseline_item_id: `l2_prop_l2_mapper_terminal_activation_family_v1_nm1_measurement_r1`
- latency_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_b128_f64: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_b128_f64: `8.272800000000001e-10` -> `6.0696e-10` mJ
- latency_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_b256_f256: `0.016634` -> `0.012438` ms
- energy_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_b256_f256: `5.988240000000001e-09` -> `4.47768e-09` mJ
- latency_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_flatten_b128_2x4x8: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1_sigmoidproxy/hier_macro/sigmoid_vec_flatten_b128_2x4x8: `8.272800000000001e-10` -> `6.0696e-10` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
