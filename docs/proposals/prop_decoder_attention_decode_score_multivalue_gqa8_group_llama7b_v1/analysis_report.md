# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1`
- `l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1_run_3b78069569b1754a`
- source commit: `8e12a8102aadb2ee332422e172d7805528b31374`
- review: PR #1352

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `llama7b_gqa8_folded_lane_equivalence_pass`
- summary: Llama7B GQA8 folded query-head lane direct RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json: decision=llama7b_gqa8_folded_lane_equivalence_pass; equivalence_pass=True; precision_contract=exact_signed_int8_qkv_s32_score_lut_softmax_integer_output; query_heads_per_kv=8; tested_parallel_query_head_lanes=[1, 2, 4, 8]; shared_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; all_lane_result_hashes_match=True; latency_best_parallel_query_head_lanes=8; latency_best_completion_cycles=58845; lane_point_count=4; lane_cycles=1:66671,2:62199,4:59963,8:58845.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Llama7B GQA8 folded query-head lane direct RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json: decision=llama7b_gqa8_folded_lane_equivalence_pass; equivalence_pass=True; precision_contract=exact_signed_int8_qkv_s32_score_lut_softmax_integer_output; query_heads_per_kv=8; tested_parallel_query_head_lanes=[1, 2, 4, 8]; shared_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; all_lane_result_hashes_match=True; latency_best_parallel_query_head_lanes=8; latency_best_completion_cycles=58845; lane_point_count=4; lane_cycles=1:66671,2:62199,4:59963,8:58845.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Llama7B GQA8 folded query-head lane direct RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json: decision=llama7b_gqa8_folded_lane_equivalence_pass; equivalence_pass=True; precision_contract=exact_signed_int8_qkv_s32_score_lut_softmax_integer_output; query_heads_per_kv=8; tested_parallel_query_head_lanes=[1, 2, 4, 8]; shared_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; all_lane_result_hashes_match=True; latency_best_parallel_query_head_lanes=8; latency_best_completion_cycles=58845; lane_point_count=4; lane_cycles=1:66671,2:62199,4:59963,8:58845.
- next_action: inspect follow-on work after l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1
