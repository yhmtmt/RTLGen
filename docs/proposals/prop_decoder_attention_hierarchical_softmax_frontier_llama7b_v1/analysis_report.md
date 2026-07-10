# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1`
- `l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1_run_ecf327e57d2035b0`
- source commit: `638989e3b2353bf1fe41c55c51fdc25246359cf2`
- review: PR #1255

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `attention_two_pass_stream_equivalence_pass`
- summary: Two-pass external-memory stream equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_stream_equivalence__l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_stream_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; score_storage=external_ready_valid_sram; kv_replay=external_ready_valid_stream; block_counts=[4, 8]; div_lanes_per_cycle=[1, 2, 4, 8]; scenarios=['always_ready', 'memory_stalls', 'result_backpressure'].

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Two-pass external-memory stream equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_stream_equivalence__l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_stream_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; score_storage=external_ready_valid_sram; kv_replay=external_ready_valid_stream; block_counts=[4, 8]; div_lanes_per_cycle=[1, 2, 4, 8]; scenarios=['always_ready', 'memory_stalls', 'result_backpressure'].

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Two-pass external-memory stream equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_stream_equivalence__l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_stream_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; score_storage=external_ready_valid_sram; kv_replay=external_ready_valid_stream; block_counts=[4, 8]; div_lanes_per_cycle=[1, 2, 4, 8]; scenarios=['always_ready', 'memory_stalls', 'result_backpressure'].
- next_action: inspect follow-on work after l2_decoder_attention_two_pass_stream_rtl_equivalence_llama7b_v1
