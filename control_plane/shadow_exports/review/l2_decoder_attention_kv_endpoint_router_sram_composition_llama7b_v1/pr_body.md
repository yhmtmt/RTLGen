## Summary
- item_id: `l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1_run_822a7fa4bc175e72`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_router_sram_composition_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e48f72f591877a376d9d84ae381df12a105baeed`
- review_metadata_source_commit: `e48f72f591877a376d9d84ae381df12a105baeed`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_router_sram_composition`
- comparison_role: `frontier_validation`
- expected_direction: `quantify_onchip_endpoint_router_sram_composition_gaps`
- expected_reason: `The result should identify whether endpoint PPA width, router width, FIFO width, and SRAM capacity are closed or require follow-on PPA.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which endpoint/router/SRAM parts of the current Llama7B frontier are physically backed, lane-scaled, or still abstract?`
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
