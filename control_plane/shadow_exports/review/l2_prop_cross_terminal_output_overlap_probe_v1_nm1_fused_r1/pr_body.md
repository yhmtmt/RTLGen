## Summary
- item_id: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1`
- run_key: `l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1_run_32962e9d6fc0fc1e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_cross_terminal_output_overlap_probe_v1_nm1_fused_r1.json`

## Developer Context
- proposal_id: `prop_cross_terminal_output_overlap_probe_v1`
- proposal_path: `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1`
- reviewer_first_read: `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1` plus `docs/developer_agent_review.md`

## Focused Comparison
- primary_question: `Does fused terminal output show a measurable benefit once the comparison is restricted to a terminal-output-sensitive proof setup rather than the original tiny softmax-tail benchmark alone?`
- proposal_outcome: `regressed`
- comparison_summary: `Focused comparison regressed latency and/or energy versus the matched baseline rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1`
- latency_delta fp16_nm1_softmax_r4/flat_nomacro: `0.000621` -> `0.0008037500000000001` ms
- energy_delta fp16_nm1_softmax_r4/flat_nomacro: `1.1462914800000001e-07` -> `1.48362605e-07` mJ
- latency_delta fp16_nm1_softmax_r4/hier_macro: `0.000621` -> `0.0008037500000000001` ms
- energy_delta fp16_nm1_softmax_r4/hier_macro: `1.2585186e-07` -> `1.6288797499999998e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
