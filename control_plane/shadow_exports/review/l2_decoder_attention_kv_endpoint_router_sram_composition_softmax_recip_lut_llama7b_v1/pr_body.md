## Summary
- item_id: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_run_9be6a888d23ca3cf`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `5dc2e285c0f0362453773f464359a35ffc0a8cb2`
- review_metadata_source_commit: `5dc2e285c0f0362453773f464359a35ffc0a8cb2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_router_sram_composition`
- comparison_role: `frontier_closure`
- expected_direction: `close_recip_lut_endpoint_router_sram_composition_for_selected_frontier`
- expected_reason: `Use reciprocal-LUT ready/valid output and q12 endpoint service frontier to audit concrete endpoint/router/SRAM composition.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does concrete endpoint/router/SRAM composition expose a width, replication, queue, or SRAM area gap that changes the selected Llama7B reciprocal-LUT frontier?`
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
