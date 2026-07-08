## Summary
- item_id: `l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1`
- run_key: `l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1_run_a6c628b0eb7aeb4b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c6dc69bd7982f988ccc231f6cbfd3438d3fd9b74`
- review_metadata_source_commit: `c892ca1f7545ec2d0391ddd299d88593e1e2710f`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_hbm_controller_replay`
- comparison_role: `score32_hbm_controller_replay`
- expected_direction: `replace_analytic_hbm_service_with_controller_replay`
- expected_reason: `The result should show whether deterministic HBM controller replay changes the score32 schedule-wrapper latency, energy, and remaining-abstraction account.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 HBM controller replay evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_hbm_controller_replay__l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json: decision=score32_hbm_controller_replay_compute_dominant; best_latency_us=12814.257853; best_latency_token_throughput_per_s=78.038073798; best_latency_total_energy_mj_per_token=467.189908559; best_latency_hbm_dominates_tile=False; best_latency_row_miss_count=64; best_requested_row_latency_us=12814.257853; compute_power_mw_source=25979.6; hbm_energy_source=134.280615241; remaining_abstractions=['controller replay is deterministic cycle-level, not RTL timing', 'vendor HBM current signoff is not represented'].`

## Focused Comparison
- primary_question: `Does replacing analytic score32 HBM service with deterministic cycle-level controller replay materially move the precision-safe Llama7B throughput or energy point?`
- comparison_role: `score32_hbm_controller_replay`
- proposal_outcome: `score32_hbm_controller_replay_compute_dominant`
- comparison_summary: `Decoder score32 HBM controller replay evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_hbm_controller_replay__l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json: decision=score32_hbm_controller_replay_compute_dominant; best_latency_us=12814.257853; best_latency_token_throughput_per_s=78.038073798; best_latency_total_energy_mj_per_token=467.189908559; best_latency_hbm_dominates_tile=False; best_latency_row_miss_count=64; best_requested_row_latency_us=12814.257853; compute_power_mw_source=25979.6; hbm_energy_source=134.280615241; remaining_abstractions=['controller replay is deterministic cycle-level, not RTL timing', 'vendor HBM current signoff is not represented'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
