## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2`
- run_key: `l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2_run_9219c8503bd5ab67`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `793c8f68e8b46d5bedbe391a887622f2fe371382`
- review_metadata_source_commit: `dfad904e398770035cf5bd449e3641879c53f03f`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_decode_score_multivalue_gqa_group_equivalence`
- comparison_role: `gqa8_direct_flat_rtl_semantic_gate`
- expected_direction: `prove_gqa8_shared_kv_direct_flat_rtl_equivalence`
- expected_reason: `Integrated eight-cluster score tensors, shared value requests, and ordered result beats must match the perf/reference model.`
- expectation_status: `unspecified`
- evaluation_summary: `Llama7B GQA8 shared-K/V direct flat RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_group_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2.json: decision=llama7b_gqa8_shared_kv_equivalence_pass; equivalence_pass=True; arithmetic_equivalence_pass=True; shared_inputs_pass=True; query_heads_per_kv=8; head_dim=128; group_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; semantic_profile=decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1; wrapper_protocol_sharing_and_order_pass=True; proof=direct_flat_rtl; compositional_proof_method=flat_8_cluster_rtl_plus_per_head_reference_and_protocol; flat_8_cluster_rtl_simulation_run=True; flat_8_cluster_equivalence_pass=True; flat_8_cluster_simulation_proof=True.`

## Focused Comparison
- primary_question: `How do area, timing, and KV service demand change when one complete Llama7B GQA8 group is embodied instead of pricing eight query heads as independent value consumers?`
- comparison_role: `gqa8_direct_flat_rtl_semantic_gate`
- proposal_outcome: `llama7b_gqa8_shared_kv_equivalence_pass`
- comparison_summary: `Llama7B GQA8 shared-K/V direct flat RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_gqa_group_equivalence__l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v2.json: decision=llama7b_gqa8_shared_kv_equivalence_pass; equivalence_pass=True; arithmetic_equivalence_pass=True; shared_inputs_pass=True; query_heads_per_kv=8; head_dim=128; group_result_sha256=e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069; semantic_profile=decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_v1; wrapper_protocol_sharing_and_order_pass=True; proof=direct_flat_rtl; compositional_proof_method=flat_8_cluster_rtl_plus_per_head_reference_and_protocol; flat_8_cluster_rtl_simulation_run=True; flat_8_cluster_equivalence_pass=True; flat_8_cluster_simulation_proof=True.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
