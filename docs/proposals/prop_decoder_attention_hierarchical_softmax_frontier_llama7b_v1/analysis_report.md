# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1`
- `l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1_run_04a9ff06d7526af6`
- source commit: `1e00b8d5a1e74eb8fc9b7209b844b609844e6a43`
- review: PR #1253

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `attention_two_pass_equivalence_pass`
- summary: Two-pass attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_global_max_equivalence__l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; block_counts=[4, 8]; command_count=3; scenarios=['always_ready', 'result_backpressure']; gates={'exact_exp_sum': True, 'exact_global_max': True, 'exact_ready_valid_schedule': True, 'exact_weighted_value': True}; remaining_abstractions=['bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports', 'final divider lane folding and full 16384-block scheduling require physical exploration'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Two-pass attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_global_max_equivalence__l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; block_counts=[4, 8]; command_count=3; scenarios=['always_ready', 'result_backpressure']; gates={'exact_exp_sum': True, 'exact_global_max': True, 'exact_ready_valid_schedule': True, 'exact_weighted_value': True}; remaining_abstractions=['bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports', 'final divider lane folding and full 16384-block scheduling require physical exploration'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Two-pass attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_global_max_equivalence__l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; block_counts=[4, 8]; command_count=3; scenarios=['always_ready', 'result_backpressure']; gates={'exact_exp_sum': True, 'exact_global_max': True, 'exact_ready_valid_schedule': True, 'exact_weighted_value': True}; remaining_abstractions=['bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports', 'final divider lane folding and full 16384-block scheduling require physical exploration'].
- next_action: inspect follow-on work after l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1
