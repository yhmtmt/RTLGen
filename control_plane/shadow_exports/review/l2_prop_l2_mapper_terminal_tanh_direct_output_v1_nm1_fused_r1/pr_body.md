## Summary
- item_id: `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1_run_b01600a408e657fc`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_tanh_direct_output_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_tanh_direct_output_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_tanh_direct_output_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- abstraction_layer: `full_architecture`
- comparison_role: `candidate`
- expected_direction: `improved`
- expected_reason: `direct vec-op output should remove the final activation-SRAM writeback roundtrip on the bounded tanh suite`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `Does bounded terminal tanh direct vec-op output improve latency and energy on fixed nm1 against the non-fused baseline?`
- comparison_role: `candidate`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_terminal_tanh_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1`
- baseline_item_id: `l2_prop_l2_mapper_terminal_tanh_direct_output_v1_nm1_measurement_r1`
- latency_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_b128_f64: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_b128_f64: `8.22684e-10` -> `6.03588e-10` mJ
- latency_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_b256_f256: `0.016634` -> `0.012438` ms
- energy_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_b256_f256: `5.954972e-09` -> `4.452804e-09` mJ
- latency_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_flatten_b128_2x4x8: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1_tanhproxy/hier_macro/tanh_vec_flatten_b128_2x4x8: `8.22684e-10` -> `6.03588e-10` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
