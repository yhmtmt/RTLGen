# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_separated_cluster_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_separated_cluster_equivalence_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_separated_cluster_equivalence_llama7b_v1`
- `l2_decoder_attention_separated_cluster_equivalence_llama7b_v1_run_ceb654dd3e3eb22c`
- source commit: `6efe80945e1c3a2424a7f25fa532f5b2a3c7cd60`
- review: PR #1248

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `attention_separated_cluster_equivalence_pass`
- summary: Separated attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_cluster_equivalence__l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json: decision=attention_separated_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_w16_exp_lut_div_b20; ratios=['1:1', '2:1', '4:1', '8:1', '4:2', '8:2']; command_count=8; scenarios=['always_ready', 'intermittent_consumer_stall', 'all_consumers_blocked_temporarily', 'result_backpressure']; gates={'exact_ready_valid_schedule': True, 'exact_score_rows': True, 'exact_softmax_weights': True, 'exact_weighted_value_vectors': True, 'loss_or_duplication': False}; remaining_abstractions=['the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions', 'PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe']; next_step=Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Separated attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_cluster_equivalence__l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json: decision=attention_separated_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_w16_exp_lut_div_b20; ratios=['1:1', '2:1', '4:1', '8:1', '4:2', '8:2']; command_count=8; scenarios=['always_ready', 'intermittent_consumer_stall', 'all_consumers_blocked_temporarily', 'result_backpressure']; gates={'exact_ready_valid_schedule': True, 'exact_score_rows': True, 'exact_softmax_weights': True, 'exact_weighted_value_vectors': True, 'loss_or_duplication': False}; remaining_abstractions=['the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions', 'PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe']; next_step=Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Separated attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_cluster_equivalence__l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json: decision=attention_separated_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_w16_exp_lut_div_b20; ratios=['1:1', '2:1', '4:1', '8:1', '4:2', '8:2']; command_count=8; scenarios=['always_ready', 'intermittent_consumer_stall', 'all_consumers_blocked_temporarily', 'result_backpressure']; gates={'exact_ready_valid_schedule': True, 'exact_score_rows': True, 'exact_softmax_weights': True, 'exact_weighted_value_vectors': True, 'loss_or_duplication': False}; remaining_abstractions=['the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions', 'PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe']; next_step=Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios.
- next_action: inspect follow-on work after l2_decoder_attention_separated_cluster_equivalence_llama7b_v1
