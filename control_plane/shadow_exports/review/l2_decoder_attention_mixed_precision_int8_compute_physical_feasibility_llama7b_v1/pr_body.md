## Summary
- item_id: `l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1_run_7c3cfc94b24af65b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_precision_int8_compute_physical_feasibility_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `bc25e1758ad1d3fa1c436584db498c5d9fc653d4`
- review_metadata_source_commit: `bc25e1758ad1d3fa1c436584db498c5d9fc653d4`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_precision_int8_compute_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `close_dual_stream_area_gap_with_int8_compute`
- expected_reason: `The job should report whether measured signed-int8 dense compute removes the dual_mac compute-area deficit under the same quality-gated mixed-precision schedule.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does measured int8 dense compute make the Q8/K8/V6 dual_mac Llama7B schedule physically feasible under the same schedule?`
- comparison_role: `frontier_closure`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
