## Summary
- item_id: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1`
- run_key: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1_run_14b437283f505b8e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4e2d585544b8b9ad7335950f741e23704e94dff4`
- review_metadata_source_commit: `4e2d585544b8b9ad7335950f741e23704e94dff4`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_endpoint_full_onchip_service_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `refine_endpoint_full_search_frontier_with_explicit_onchip_service_policies`
- expected_reason: `Identify the best explicit on-chip service policy and report movement versus the endpoint full-search cap-aware frontier without changing HBM/DRAM assumptions.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `How does the current cap-aware endpoint full-search Llama7B frontier move under explicit on-chip service policy modeling?`
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
