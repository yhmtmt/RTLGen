## Summary
- item_id: `l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1_run_885dadea60c80c63`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_ready_valid_service_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_ready_valid_service_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_ready_valid_service_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4d2610ebb9bb345bdb43770b40ae5c9a1f56b441`
- review_metadata_source_commit: `4d2610ebb9bb345bdb43770b40ae5c9a1f56b441`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_ready_valid_service`
- comparison_role: `frontier_validation`
- expected_direction: `validate_selected_endpoint_service_policy_with_ready_valid_rtl`
- expected_reason: `The result should report derived DATA_W, BANKS, endpoint queue depth, bank queue depth, backpressure counters, occupancy maxima, and pass/fail decision.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the current least-abstract Llama7B endpoint service point have a concrete ready/valid endpoint implementation for the selected packet and queue sizing?`
- comparison_role: `frontier_validation`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
