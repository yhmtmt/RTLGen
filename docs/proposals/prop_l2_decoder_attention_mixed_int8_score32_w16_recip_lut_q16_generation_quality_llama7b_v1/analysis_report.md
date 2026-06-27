# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1`
- `l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1_run_3fd627aa47bec8ec`
- source commit: `ae02ff76de4a6b5039eec31e25a1fa2e6a1384cd`
- review: PR #1053

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_generation_quality_hold`
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality__l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_hold; candidate_id=score32_w16_rtl_recip_q16; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality__l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_hold; candidate_id=score32_w16_rtl_recip_q16; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality__l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_hold; candidate_id=score32_w16_rtl_recip_q16; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score32_w16_recip_lut_q16_generation_quality_llama7b_v1
