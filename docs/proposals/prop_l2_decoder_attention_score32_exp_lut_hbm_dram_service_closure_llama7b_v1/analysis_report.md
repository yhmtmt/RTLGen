# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
- `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1_run_b4033016c25d2334`
- source commit: `7270e2c9e95e17b1adb592ca35e4a3e313357dff`
- review: PR #1203

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_exp_lut_hbm_dram_service_closure_hbm_sensitive`
- summary: Decoder score32 exp-LUT HBM/DRAM service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_hbm_dram_service_closure__l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json: decision=score32_exp_lut_hbm_dram_service_closure_hbm_sensitive; best_latency_us=12532.357427; best_latency_token_throughput_per_s=79.793447149; best_latency_hbm_energy_mj_per_token=134.280615241; best_energy_hbm_energy_mj_per_token=134.280615241; source_score32_latency_us=12519.342352; source_controller_service_cycles=1301; remaining_abstractions=['cycle_accurate_hbm_controller_rtl', 'hbm_vendor_current_signoff'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 exp-LUT HBM/DRAM service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_hbm_dram_service_closure__l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json: decision=score32_exp_lut_hbm_dram_service_closure_hbm_sensitive; best_latency_us=12532.357427; best_latency_token_throughput_per_s=79.793447149; best_latency_hbm_energy_mj_per_token=134.280615241; best_energy_hbm_energy_mj_per_token=134.280615241; source_score32_latency_us=12519.342352; source_controller_service_cycles=1301; remaining_abstractions=['cycle_accurate_hbm_controller_rtl', 'hbm_vendor_current_signoff'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 exp-LUT HBM/DRAM service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_hbm_dram_service_closure__l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json: decision=score32_exp_lut_hbm_dram_service_closure_hbm_sensitive; best_latency_us=12532.357427; best_latency_token_throughput_per_s=79.793447149; best_latency_hbm_energy_mj_per_token=134.280615241; best_energy_hbm_energy_mj_per_token=134.280615241; source_score32_latency_us=12519.342352; source_controller_service_cycles=1301; remaining_abstractions=['cycle_accurate_hbm_controller_rtl', 'hbm_vendor_current_signoff'].
- next_action: inspect follow-on work after l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1
