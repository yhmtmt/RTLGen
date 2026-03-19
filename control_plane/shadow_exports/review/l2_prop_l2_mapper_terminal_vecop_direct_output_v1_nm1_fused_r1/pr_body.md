## Summary
- item_id: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1`
- run_key: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1_run_9ca3905be8de3980`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `Direct terminal vec-op output should reduce the final writeback tail on at least part of the bounded standalone terminal ReLU suite.`
- expectation_status: `as_expected`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `Can a bounded terminal vec-op family establish clean nm1 reference points first, then show a direct-output win on those same points without reopening broader ranking?`
- comparison_role: `candidate`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`
- baseline_item_id: `l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2`
- latency_delta fp16_nm1/flat_nomacro/relu_vec_b128_f64: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1/flat_nomacro/relu_vec_b128_f64: `4.43794356e-07` -> `3.25603692e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/relu_vec_b256_f256: `0.016634` -> `0.012438` ms
- energy_delta fp16_nm1/flat_nomacro/relu_vec_b256_f256: `3.212391348e-06` -> `2.402051436e-06` mJ
- latency_delta fp16_nm1/flat_nomacro/relu_vec_flatten_b128_2x4x8: `0.0022979999999999997` -> `0.001686` ms
- energy_delta fp16_nm1/flat_nomacro/relu_vec_flatten_b128_2x4x8: `4.43794356e-07` -> `3.25603692e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
