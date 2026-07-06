# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_compute_activity_energy_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1`
- `l2_decoder_attention_score32_compute_activity_energy_llama7b_v1_run_a695f985b7bd8ec0`
- source commit: `089e8c6c1e2286701bf758caf99703a081a12f51`
- review: PR #1209

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_compute_activity_energy_still_energy_worse`
- summary: Decoder score32 compute-activity energy evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_compute_activity_energy__l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json: decision=score32_compute_activity_energy_still_energy_worse; compute_active_duty=0.957495485; wall_time_compute_energy_mj_per_token=360.550392645; best_clock_gated_compute_energy_mj_per_token=345.225372946; best_clock_gated_total_energy_mj_per_token=479.505988187; energy_reduction_fraction_vs_wall_time=0.030970209; clock_gated_score32_vs_measured_fp16_energy_ratio=5.871684274; score32_latency_us=12532.357427; recommended_next_step=Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax datapath variants or quality-close a lower-energy mixed/int8 path.; remaining_abstractions=['compute active duty is derived from L2 cycle accounting, not RTL toggle activity', 'idle power fractions are analytic clock-gating scenarios, not gate-level power simulation'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 compute-activity energy evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_compute_activity_energy__l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json: decision=score32_compute_activity_energy_still_energy_worse; compute_active_duty=0.957495485; wall_time_compute_energy_mj_per_token=360.550392645; best_clock_gated_compute_energy_mj_per_token=345.225372946; best_clock_gated_total_energy_mj_per_token=479.505988187; energy_reduction_fraction_vs_wall_time=0.030970209; clock_gated_score32_vs_measured_fp16_energy_ratio=5.871684274; score32_latency_us=12532.357427; recommended_next_step=Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax datapath variants or quality-close a lower-energy mixed/int8 path.; remaining_abstractions=['compute active duty is derived from L2 cycle accounting, not RTL toggle activity', 'idle power fractions are analytic clock-gating scenarios, not gate-level power simulation'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 compute-activity energy evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_compute_activity_energy__l2_decoder_attention_score32_compute_activity_energy_llama7b_v1.json: decision=score32_compute_activity_energy_still_energy_worse; compute_active_duty=0.957495485; wall_time_compute_energy_mj_per_token=360.550392645; best_clock_gated_compute_energy_mj_per_token=345.225372946; best_clock_gated_total_energy_mj_per_token=479.505988187; energy_reduction_fraction_vs_wall_time=0.030970209; clock_gated_score32_vs_measured_fp16_energy_ratio=5.871684274; score32_latency_us=12532.357427; recommended_next_step=Clock gating does not erase the score32 energy gap; prioritize lower-power score32/softmax datapath variants or quality-close a lower-energy mixed/int8 path.; remaining_abstractions=['compute active duty is derived from L2 cycle accounting, not RTL toggle activity', 'idle power fractions are analytic clock-gating scenarios, not gate-level power simulation'].
- next_action: inspect follow-on work after l2_decoder_attention_score32_compute_activity_energy_llama7b_v1
