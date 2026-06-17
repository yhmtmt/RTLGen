## Summary
- item_id: `l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1_run_939bee681de4c92a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_sram_noc_softmax_recip_lut_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_sram_noc_softmax_recip_lut_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_sram_noc_softmax_recip_lut_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `24e04c7e691f2f6ad5b44d2db02568474fb550a5`
- review_metadata_source_commit: `24e04c7e691f2f6ad5b44d2db02568474fb550a5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_sram_noc_full_search_softmax_recip_lut_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `rank_q8_q10_q12_softmax_profiles_in_endpoint_sram_noc_frontier`
- expected_reason: `Rank q8/q10/q12 reciprocal-LUT softmax local-cost profiles under practical endpoint SRAM/NoC caps.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `After q8 standalone reciprocal-LUT softmax PPA is available, does the practical endpoint SRAM/NoC full search select q8, q10, or q12 as the best measured softmax precision point?`
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
