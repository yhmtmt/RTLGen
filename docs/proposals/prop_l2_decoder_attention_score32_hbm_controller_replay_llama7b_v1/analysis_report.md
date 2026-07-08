# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1`
- `l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1_run_a6c628b0eb7aeb4b`
- source commit: `c6dc69bd7982f988ccc231f6cbfd3438d3fd9b74`
- review: PR #1226

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_hbm_controller_replay_compute_dominant`
- summary: Decoder score32 HBM controller replay evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_hbm_controller_replay__l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json: decision=score32_hbm_controller_replay_compute_dominant; best_latency_us=12814.257853; best_latency_token_throughput_per_s=78.038073798; best_latency_total_energy_mj_per_token=467.189908559; best_latency_hbm_dominates_tile=False; best_latency_row_miss_count=64; best_requested_row_latency_us=12814.257853; compute_power_mw_source=25979.6; hbm_energy_source=134.280615241; remaining_abstractions=['controller replay is deterministic cycle-level, not RTL timing', 'vendor HBM current signoff is not represented'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 HBM controller replay evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_hbm_controller_replay__l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json: decision=score32_hbm_controller_replay_compute_dominant; best_latency_us=12814.257853; best_latency_token_throughput_per_s=78.038073798; best_latency_total_energy_mj_per_token=467.189908559; best_latency_hbm_dominates_tile=False; best_latency_row_miss_count=64; best_requested_row_latency_us=12814.257853; compute_power_mw_source=25979.6; hbm_energy_source=134.280615241; remaining_abstractions=['controller replay is deterministic cycle-level, not RTL timing', 'vendor HBM current signoff is not represented'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 HBM controller replay evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_hbm_controller_replay__l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json: decision=score32_hbm_controller_replay_compute_dominant; best_latency_us=12814.257853; best_latency_token_throughput_per_s=78.038073798; best_latency_total_energy_mj_per_token=467.189908559; best_latency_hbm_dominates_tile=False; best_latency_row_miss_count=64; best_requested_row_latency_us=12814.257853; compute_power_mw_source=25979.6; hbm_energy_source=134.280615241; remaining_abstractions=['controller replay is deterministic cycle-level, not RTL timing', 'vendor HBM current signoff is not represented'].
- next_action: inspect follow-on work after l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1
