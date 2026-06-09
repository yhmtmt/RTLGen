## Summary
- item_id: `l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1`
- run_key: `l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1_run_351be7b83eec6af3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `04c0f002707e1c7453a396fd4073f5a2c7bc788e`
- review_metadata_source_commit: `04c0f002707e1c7453a396fd4073f5a2c7bc788e`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_onchip_service_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `refine_dense_tile_scheduler_frontier_with_onchip_service_policies`
- expected_reason: `The result should identify the best on-chip schedule/bank/queue/router policy and report slowdown versus the SRAM/NoC cap result without changing HBM/DRAM assumptions.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `How does the Llama7B dense-tile frontier move when SRAM bank arbitration, endpoint queues, router latency, packet payload, and on-chip scheduling policy are modeled explicitly, excluding HBM/DRAM changes?`
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
