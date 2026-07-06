## Summary
- item_id: `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1`
- run_key: `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1_run_a695f985b7bd8ec0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_compute_activity_energy_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_compute_activity_energy_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_compute_activity_energy_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_compute_activity_energy_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `089e8c6c1e2286701bf758caf99703a081a12f51`
- review_metadata_source_commit: `d9c05a6def61ebddae647a65ced20c63d0e9f27c`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_compute_activity_energy`
- comparison_role: `score32_compute_activity_energy_closure`
- expected_direction: `record_score32_compute_activity_energy`
- expected_reason: `State whether active-cycle/clock-gating accounting changes the score32 energy ranking versus the measured exact-FP16 reference.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 compute-activity energy evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_compute_activity_energy__l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json: decision=score32_compute_activity_energy_still_energy_worse; compute_active_duty=0.957495485; wall_time_compute_energy_mj_per_token=360.550392645; best_clock_gated_compute_energy_mj_per_token=345.225372946; best_clock_gated_total_energy_mj_per_token=479.505988187; energy_reduction_fraction_vs_wall_time=0.030970209; clock_gated_score32_vs_measured_fp16_energy_ratio=5.871684274; score32_latency_us=12532.357427; recommended_next_step=Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax datapath variants or quality-close a lower-energy mixed/int8 path.; remaining_abstractions=['compute active duty is derived from L2 cycle accounting, not RTL toggle activity', 'idle power fractions are analytic clock-gating scenarios, not gate-level power simulation'].`

## Focused Comparison
- primary_question: `Does clock-gating/active-cycle accounting materially reduce score32 energy enough to change the current Llama7B energy ranking?`
- comparison_role: `score32_compute_activity_energy_closure`
- proposal_outcome: `score32_compute_activity_energy_still_energy_worse`
- comparison_summary: `Decoder score32 compute-activity energy evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_compute_activity_energy__l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json: decision=score32_compute_activity_energy_still_energy_worse; compute_active_duty=0.957495485; wall_time_compute_energy_mj_per_token=360.550392645; best_clock_gated_compute_energy_mj_per_token=345.225372946; best_clock_gated_total_energy_mj_per_token=479.505988187; energy_reduction_fraction_vs_wall_time=0.030970209; clock_gated_score32_vs_measured_fp16_energy_ratio=5.871684274; score32_latency_us=12532.357427; recommended_next_step=Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax datapath variants or quality-close a lower-energy mixed/int8 path.; remaining_abstractions=['compute active duty is derived from L2 cycle accounting, not RTL toggle activity', 'idle power fractions are analytic clock-gating scenarios, not gate-level power simulation'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
