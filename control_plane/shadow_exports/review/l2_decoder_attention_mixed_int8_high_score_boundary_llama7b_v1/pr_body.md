## Summary
- item_id: `l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1_run_4644b3dd2daf2900`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `766efa521cd4c39c33d52b3294c381a61ea09c95`
- review_metadata_source_commit: `766efa521cd4c39c33d52b3294c381a61ea09c95`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_high_score_boundary`
- comparison_role: `precision_boundary`
- expected_direction: `find_high_score_precision_boundary`
- expected_reason: `Score10-16 all failed while the earlier high-resolution QKV8 path passed; this job narrows whether score18/20/22 can preserve rankings or whether only near-full score precision is viable.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_high_score_boundary__l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_pass; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=16; top1_match_rate=1.0; topk_contains_rate=1.0; mean_logit_cosine=0.9999591095634982; mean_probability_kl=0.0005788093087387277; max_abs_logit_delta_max=0.4375; next_step=Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.; best_candidate_id=score24_float; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9999591095634982; best_mean_probability_kl=0.0005788093087387277; candidate_count=9.`

## Focused Comparison
- primary_question: `What is the lowest high-score precision that preserves native 7B-class checkpoint rankings for QKV8 attention?`
- comparison_role: `precision_boundary`
- proposal_outcome: `mixed_int8_native_attention_shadow_pass`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_high_score_boundary__l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_pass; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=16; top1_match_rate=1.0; topk_contains_rate=1.0; mean_logit_cosine=0.9999591095634982; mean_probability_kl=0.0005788093087387277; max_abs_logit_delta_max=0.4375; next_step=Proceed to broader mixed/int8 attention native-checkpoint checks before frontier scheduling.; best_candidate_id=score24_float; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9999591095634982; best_mean_probability_kl=0.0005788093087387277; candidate_count=9.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
