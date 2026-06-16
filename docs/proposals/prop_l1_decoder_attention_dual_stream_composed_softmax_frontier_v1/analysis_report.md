# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1`
- `candidate_id`: `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`
- `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1_run_70af86414c940825`
- source commit: `2634eede3c91b2c85d339784ed630f7fecdfc514`
- review: PR #862

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_precision_quality_blocked`
- summary: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json: decision=mixed_precision_quality_blocked; best_quality_candidate=q8_k8_v6_a24_s8_w8_softmax_rtl_exact; best_quality_decision=mixed_precision_risky; best_low_cost_candidate=None; best_low_cost_decision=None; passing_candidate_count=0; borderline_candidate_count=0; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json: decision=mixed_precision_quality_blocked; best_quality_candidate=q8_k8_v6_a24_s8_w8_softmax_rtl_exact; best_quality_decision=mixed_precision_risky; best_low_cost_candidate=None; best_low_cost_decision=None; passing_candidate_count=0; borderline_candidate_count=0; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json: decision=mixed_precision_quality_blocked; best_quality_candidate=q8_k8_v6_a24_s8_w8_softmax_rtl_exact; best_quality_decision=mixed_precision_risky; best_low_cost_candidate=None; best_low_cost_decision=None; passing_candidate_count=0; borderline_candidate_count=0; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery.
- next_action: inspect follow-on work after l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1
