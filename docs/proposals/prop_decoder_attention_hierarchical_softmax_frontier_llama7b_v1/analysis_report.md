# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1`
- `l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1_run_b95116cc4c39841a`
- source commit: `275673eb674626455a988b848941edbf28fd02cd`
- review: PR #1273

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `score32_exp_lut_sram_hierarchy_envelope_changes_frontier`
- summary: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_changes_frontier; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=29.015625; nominal_hbm_byte_share=0.992916107; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=16.265625; conservative_hbm_byte_share=0.9960289; conservative_hbm_share_delta=0.012630462; conservative_projected_latency_us_hbm_share_scaled=12680.136872; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_changes_frontier; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=29.015625; nominal_hbm_byte_share=0.992916107; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=16.265625; conservative_hbm_byte_share=0.9960289; conservative_hbm_share_delta=0.012630462; conservative_projected_latency_us_hbm_share_scaled=12680.136872; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_changes_frontier; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=29.015625; nominal_hbm_byte_share=0.992916107; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=16.265625; conservative_hbm_byte_share=0.9960289; conservative_hbm_share_delta=0.012630462; conservative_projected_latency_us_hbm_share_scaled=12680.136872; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.
- next_action: inspect follow-on work after l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1
