## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v3`
- run_key: `l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v3_run_6624fee1a9a15cd6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v3/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v3.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `48e6b91d0af1d97a8fd7bc6863ce6fcf75707f23`
- review_metadata_source_commit: `6afdd43402310540fa077bd88b75245afdcb8718`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster_activity_power`
- comparison_role: `shared_score_multivalue_cluster_activity_power_gate`
- expected_direction: `record_shared_score_multivalue_cluster_activity_power_gate`
- expected_reason: `v3 records diagnostic evidence for macro activity provenance, zero-toggle filtering, and non-finite OpenSTA power while retaining all existing gates.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the shared-score multivalue cluster remain physically interesting once evaluator-local activity evidence replaces the current vectorless-power placeholder?`
- comparison_role: `shared_score_multivalue_cluster_activity_power_gate`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
