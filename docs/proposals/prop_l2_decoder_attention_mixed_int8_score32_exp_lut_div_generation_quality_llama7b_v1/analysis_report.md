# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`
- `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1_run_eeda56dd3eb7bd46`
- source commit: `99337b77f24d954b59e1318f6c0b52b28f3cb78f`
- review: PR #1184

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_generation_quality_pass`
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_exp_lut_div; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.875; free_run_token_match_rate=0.890625; diverged_prompt_count=1; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0746646922933087; teacher_forced_mean_nll_delta=0.0008945953623444368; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44889021134685153; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_exp_lut_div; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.875; free_run_token_match_rate=0.890625; diverged_prompt_count=1; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0746646922933087; teacher_forced_mean_nll_delta=0.0008945953623444368; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44889021134685153; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality__l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_exp_lut_div; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.875; free_run_token_match_rate=0.890625; diverged_prompt_count=1; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0746646922933087; teacher_forced_mean_nll_delta=0.0008945953623444368; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44889021134685153; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1
