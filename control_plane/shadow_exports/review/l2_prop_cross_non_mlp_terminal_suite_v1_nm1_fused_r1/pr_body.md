## Summary
- item_id: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1`
- run_key: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1_run_40af2795b96518ef`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_cross_non_mlp_terminal_suite_v1`
- proposal_path: `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1`
- reviewer_first_read: `docs/developer_loop/prop_cross_non_mlp_terminal_suite_v1` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `The fused terminal-output path should reduce latency and energy relative to the refreshed non-fused nm1 suite baseline.`
- expectation_status: `as_expected`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `Does fused terminal output improve a corrected-contract non-fused nm1 reference across a small terminal-sensitive softmax-tail model slice?`
- comparison_role: `candidate`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1`
- baseline_item_id: `l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1`
- latency_delta fp16_nm1_softmax_r4/flat_nomacro: `0.006154` -> `0.004746` ms
- energy_delta fp16_nm1_softmax_r4/flat_nomacro: `1.1359545519999999e-06` -> `8.760546480000001e-07` mJ
- latency_delta fp16_nm1_softmax_r4/flat_nomacro: `0.006154` -> `0.001179` ms
- energy_delta fp16_nm1_softmax_r4/flat_nomacro: `1.1359545519999999e-06` -> `2.1762925199999998e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
