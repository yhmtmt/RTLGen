## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3`
- run_key: `l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3_run_1d3210b0b6381e1f`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_llama7b_v1_r3.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ed34e8ae8b844b444ee8f08fbcfecf8947f493af`
- review_metadata_source_commit: `ed34e8ae8b844b444ee8f08fbcfecf8947f493af`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_endpoint_topology_derived_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `How does the endpoint-measured Llama7B dense-tile schedule move when NoC service is restricted to valid endpoint topology/scheduler pairs?`
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
