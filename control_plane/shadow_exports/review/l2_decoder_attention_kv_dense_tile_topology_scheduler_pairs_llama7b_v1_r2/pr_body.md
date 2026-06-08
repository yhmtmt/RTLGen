## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2_run_819b5f07fa84b9f1`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d53541cfc58fdbf6a8fb614b6be10246fcb91c09`
- review_metadata_source_commit: `d53541cfc58fdbf6a8fb614b6be10246fcb91c09`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_topology_scheduler_pairs`
- comparison_role: `frontier_filter`
- expected_direction: `filter_topology_scheduler_pairs`
- expected_reason: `Produce a compact valid-pair matrix and topology-derived service envelopes before the next Llama7B scheduler run.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which NoC topology/scheduler/reducer/bank-placement pairs are logically valid for the dense_gemm_16x8_k1_p1 Llama7B attention frontier, and how far are their derived service envelopes from the previous abstract NoC service point?`
- comparison_role: `frontier_filter`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
