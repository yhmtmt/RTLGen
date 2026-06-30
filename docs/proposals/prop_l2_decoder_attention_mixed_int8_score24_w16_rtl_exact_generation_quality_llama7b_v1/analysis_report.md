# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2`
- `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2_run_28d4fdd536b2164b`
- source commit: `23463c027a33c181540252eeefeffc5756d6c3a7`
- review: PR #1087

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_generation_quality_hold`
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score24 w16 rtl exact mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score24 w16 rtl exact mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score24 w16 rtl exact mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2
