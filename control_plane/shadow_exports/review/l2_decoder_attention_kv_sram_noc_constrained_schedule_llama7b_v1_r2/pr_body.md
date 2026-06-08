## Summary
- item_id: `l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2_run_51de0203c0f1b0d2`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `c1c4a8a0ad135928548518554082c98e67595c77`
- review_metadata_source_commit: `c1c4a8a0ad135928548518554082c98e67595c77`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_sram_noc_constrained_schedule`
- comparison_role: `frontier_revision`
- expected_direction: `revise_dense_tile_scheduler_frontier_with_practical_sram_noc_caps`
- expected_reason: `The result should report slowdown versus topology-derived scheduling and identify whether topology, SRAM-bank service, or endpoint service caps the retained frontier.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `What is the revised Llama7B 131k dense-tile latency frontier after applying practical SRAM-bank and endpoint NoC service caps to the topology-derived schedule?`
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
