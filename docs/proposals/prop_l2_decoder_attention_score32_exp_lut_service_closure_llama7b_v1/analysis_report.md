# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1`
- `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1_run_b3e9867f98ad3184`
- source commit: `241c0c1b8daef4cf4a59a3c687d67feb5fef28e5`
- review: PR #1199

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_exp_lut_service_closure_recorded`
- summary: Decoder score32 exp-LUT service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json: decision=score32_exp_lut_service_closure_recorded; score32_supported=True; wrapper_metrics_match=True; selected_semantic_profile=score32_exp_lut_div; latency_us=12519.342352; source_latency_us=1575.373891; macs_per_cycle=104320; dominant_tile_resource=pipeline_attention; remaining_abstractions=['tile_local_and_shared_sram', 'hbm_dram_service']; requires_hbm_dram_closure=True.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 exp-LUT service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json: decision=score32_exp_lut_service_closure_recorded; score32_supported=True; wrapper_metrics_match=True; selected_semantic_profile=score32_exp_lut_div; latency_us=12519.342352; source_latency_us=1575.373891; macs_per_cycle=104320; dominant_tile_resource=pipeline_attention; remaining_abstractions=['tile_local_and_shared_sram', 'hbm_dram_service']; requires_hbm_dram_closure=True.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 exp-LUT service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json: decision=score32_exp_lut_service_closure_recorded; score32_supported=True; wrapper_metrics_match=True; selected_semantic_profile=score32_exp_lut_div; latency_us=12519.342352; source_latency_us=1575.373891; macs_per_cycle=104320; dominant_tile_resource=pipeline_attention; remaining_abstractions=['tile_local_and_shared_sram', 'hbm_dram_service']; requires_hbm_dram_closure=True.
- next_action: inspect follow-on work after l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1
