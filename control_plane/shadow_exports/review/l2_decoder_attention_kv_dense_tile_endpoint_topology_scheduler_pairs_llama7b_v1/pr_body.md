## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1_run_c2a3052f6fb28c40`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e7bfa4319ac143f60db3761a2bd1dd88a3f8744a`
- review_metadata_source_commit: `e7bfa4319ac143f60db3761a2bd1dd88a3f8744a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_endpoint_topology_scheduler_pairs`
- comparison_role: `frontier_revision`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which topology/scheduler pairs are logically valid for the endpoint-measured Llama7B dense-tile attention frontier?`
- comparison_role: `frontier_revision`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
