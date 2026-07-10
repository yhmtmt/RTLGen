# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1`
- `l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1_run_103d4896d0c3ea53`
- source commit: `7dd3b32a12c2dcc4acc528aa88dd71fd3d88ad12`
- review: PR #1251

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `two_pass_exact_selected`
- summary: Hierarchical attention composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hierarchical_softmax_architecture__l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json: decision=two_pass_exact_selected; online_pass=False; online_error_bound_q16=655; lengths=[128, 4096, 131072]; distributions=['normal_std1', 'normal_std4', 'monotonic_ramp16']; llama7b_score_buffer={'bytes': 16777216, 'current_shared_sram_mib': 68, 'fits_current_shared_sram': True, 'mib': 16.0}; width_bounds={'exp_sum_bits': 33, 'exp_sum_bits_required': 33, 'max_block_count': 16384, 'max_context_tokens': 131072, 'max_exp_sum': 8589803520, 'max_weighted_numerator_magnitude': 1099494850560, 'merge_scale_bits': 24, 'weighted_numerator_bits': 41, 'weighted_numerator_signed_bits_required': 41}; next_step=Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Hierarchical attention composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hierarchical_softmax_architecture__l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json: decision=two_pass_exact_selected; online_pass=False; online_error_bound_q16=655; lengths=[128, 4096, 131072]; distributions=['normal_std1', 'normal_std4', 'monotonic_ramp16']; llama7b_score_buffer={'bytes': 16777216, 'current_shared_sram_mib': 68, 'fits_current_shared_sram': True, 'mib': 16.0}; width_bounds={'exp_sum_bits': 33, 'exp_sum_bits_required': 33, 'max_block_count': 16384, 'max_context_tokens': 131072, 'max_exp_sum': 8589803520, 'max_weighted_numerator_magnitude': 1099494850560, 'merge_scale_bits': 24, 'weighted_numerator_bits': 41, 'weighted_numerator_signed_bits_required': 41}; next_step=Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Hierarchical attention composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hierarchical_softmax_architecture__l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json: decision=two_pass_exact_selected; online_pass=False; online_error_bound_q16=655; lengths=[128, 4096, 131072]; distributions=['normal_std1', 'normal_std4', 'monotonic_ramp16']; llama7b_score_buffer={'bytes': 16777216, 'current_shared_sram_mib': 68, 'fits_current_shared_sram': True, 'mib': 16.0}; width_bounds={'exp_sum_bits': 33, 'exp_sum_bits_required': 33, 'max_block_count': 16384, 'max_context_tokens': 131072, 'max_exp_sum': 8589803520, 'max_weighted_numerator_magnitude': 1099494850560, 'merge_scale_bits': 24, 'weighted_numerator_bits': 41, 'weighted_numerator_signed_bits_required': 41}; next_step=Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison.
- next_action: inspect follow-on work after l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1
