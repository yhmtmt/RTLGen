# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
- `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1_run_3527a58e1b41c4e9`
- source commit: `b759c0945ffb23a9f331b41e5d4d714cb58eb9c5`
- review: PR #1201

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_exp_lut_sram_hierarchy_envelope_stable`
- summary: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_stable; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=47.8125; nominal_hbm_byte_share=0.988327026; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=35.046875; conservative_hbm_byte_share=0.991443634; conservative_hbm_share_delta=0.008045196; conservative_projected_latency_us_hbm_share_scaled=12621.763263; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_stable; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=47.8125; nominal_hbm_byte_share=0.988327026; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=35.046875; conservative_hbm_byte_share=0.991443634; conservative_hbm_share_delta=0.008045196; conservative_projected_latency_us_hbm_share_scaled=12621.763263; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_stable; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=47.8125; nominal_hbm_byte_share=0.988327026; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=35.046875; conservative_hbm_byte_share=0.991443634; conservative_hbm_share_delta=0.008045196; conservative_projected_latency_us_hbm_share_scaled=12621.763263; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.
- next_action: inspect follow-on work after l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1
