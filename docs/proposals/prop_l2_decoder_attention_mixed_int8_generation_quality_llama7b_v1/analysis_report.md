# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3`
- `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3_run_daa0e970350921ef`
- source commit: `e73b2f80d545f5236fa8c67cd1ca11006a8bea0e`
- review: PR #1031

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_generation_quality_pass`
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_float; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.84375; diverged_prompt_count=2; mean_first_divergence_step=6.625; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0760980009300023; teacher_forced_mean_nll_delta=0.0023279039990386913; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44887183254036667; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_float; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.84375; diverged_prompt_count=2; mean_first_divergence_step=6.625; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0760980009300023; teacher_forced_mean_nll_delta=0.0023279039990386913; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44887183254036667; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_float; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.84375; diverged_prompt_count=2; mean_first_divergence_step=6.625; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0760980009300023; teacher_forced_mean_nll_delta=0.0023279039990386913; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44887183254036667; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3
