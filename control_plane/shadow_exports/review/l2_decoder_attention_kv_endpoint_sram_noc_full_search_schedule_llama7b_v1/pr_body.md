## Summary
- item_id: `l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1_run_965a97cece8df918`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_sram_noc_full_search_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a116a9137bf5fd73daa475c2a1931d50a2d45d53`
- review_metadata_source_commit: `a116a9137bf5fd73daa475c2a1931d50a2d45d53`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_sram_noc_full_search_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `cap_aware_full_search_over_endpoint_topology_schedule`
- expected_reason: `Check whether practical SRAM-bank and endpoint service caps change the best topology/scheduler point versus retained-frontier postprocessing.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does cap-aware full regeneration select a different best Llama7B endpoint topology/scheduler point than retained-frontier SRAM/NoC postprocessing?`
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
