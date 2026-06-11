# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_mixed_precision_quality_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- `l2_decoder_attention_mixed_precision_quality_llama7b_v1_run_b48421fdaf63879b`
- source commit: `6f0e2290ce508c9a8a90fdbb188ca3843dce173d`
- review: PR #832

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `mixed_precision_quality_candidate_found`
- summary: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json: decision=mixed_precision_quality_candidate_found; best_quality_candidate=q8_k8_v8_a24_s24_w16; best_quality_decision=mixed_precision_proxy_pass; best_low_cost_candidate=q8_k8_v6_a24_s24_w16; best_low_cost_decision=mixed_precision_proxy_pass; passing_candidate_count=3; borderline_candidate_count=1; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json: decision=mixed_precision_quality_candidate_found; best_quality_candidate=q8_k8_v8_a24_s24_w16; best_quality_decision=mixed_precision_proxy_pass; best_low_cost_candidate=q8_k8_v6_a24_s24_w16; best_low_cost_decision=mixed_precision_proxy_pass; passing_candidate_count=3; borderline_candidate_count=1; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json: decision=mixed_precision_quality_candidate_found; best_quality_candidate=q8_k8_v8_a24_s24_w16; best_quality_decision=mixed_precision_proxy_pass; best_low_cost_candidate=q8_k8_v6_a24_s24_w16; best_low_cost_decision=mixed_precision_proxy_pass; passing_candidate_count=3; borderline_candidate_count=1; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion.
- next_action: inspect follow-on work after l2_decoder_attention_mixed_precision_quality_llama7b_v1
