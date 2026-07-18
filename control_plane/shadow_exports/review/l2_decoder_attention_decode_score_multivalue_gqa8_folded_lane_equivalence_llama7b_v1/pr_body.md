## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1_run_3b78069569b1754a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `8e12a8102aadb2ee332422e172d7805528b31374`
- review_metadata_source_commit: `f63fd55c1360dcc9b072e672c8ccc0ff2234ac6b`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence`
- comparison_role: `gqa8_folded_lane_direct_rtl_semantic_gate`
- expected_direction: `prove_exact_gqa8_folded_lane_equivalence_and_replay_cost`
- expected_reason: `Folded PPA requires direct score/output equivalence with explicit Q/K and value replay.`
- expectation_status: `unspecified`
- evaluation_summary: `Llama7B GQA8 folded query-head lane direct RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json: decision=llama7b_gqa8_folded_lane_equivalence_pass; equivalence_pass=True; precision_contract=exact_signed_int8_qkv_s32_score_lut_softmax_integer_output; query_heads_per_kv=8; tested_parallel_query_head_lanes=[1, 2, 4, 8]; shared_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; all_lane_result_hashes_match=True; latency_best_parallel_query_head_lanes=8; latency_best_completion_cycles=58845; lane_point_count=4; lane_cycles=1:66671,2:62199,4:59963,8:58845.`

## Focused Comparison
- primary_question: `How do area, timing, and KV service demand change when one complete Llama7B GQA8 group is embodied instead of pricing eight query heads as independent value consumers?`
- comparison_role: `gqa8_folded_lane_direct_rtl_semantic_gate`
- proposal_outcome: `llama7b_gqa8_folded_lane_equivalence_pass`
- comparison_summary: `Llama7B GQA8 folded query-head lane direct RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1.json: decision=llama7b_gqa8_folded_lane_equivalence_pass; equivalence_pass=True; precision_contract=exact_signed_int8_qkv_s32_score_lut_softmax_integer_output; query_heads_per_kv=8; tested_parallel_query_head_lanes=[1, 2, 4, 8]; shared_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; all_lane_result_hashes_match=True; latency_best_parallel_query_head_lanes=8; latency_best_completion_cycles=58845; lane_point_count=4; lane_cycles=1:66671,2:62199,4:59963,8:58845.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
