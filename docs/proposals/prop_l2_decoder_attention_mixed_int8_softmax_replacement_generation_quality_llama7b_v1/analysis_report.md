# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`
- `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1_run_c33510d19aaf6429`
- source commit: `c697832fc58789af79c407266536866bd03aa31f`
- review: PR #1066

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_int8_generation_quality_pass`
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_softmax_replacement_generation_quality__l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=qkv8_q24_pwl_recip_q24_bucket8; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.875; diverged_prompt_count=2; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0921800072287313; teacher_forced_mean_nll_delta=0.01840991029776741; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44199434749935546; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_softmax_replacement_generation_quality__l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=qkv8_q24_pwl_recip_q24_bucket8; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.875; diverged_prompt_count=2; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0921800072287313; teacher_forced_mean_nll_delta=0.01840991029776741; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44199434749935546; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_softmax_replacement_generation_quality__l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=qkv8_q24_pwl_recip_q24_bucket8; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.875; diverged_prompt_count=2; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0921800072287313; teacher_forced_mean_nll_delta=0.01840991029776741; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44199434749935546; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1
