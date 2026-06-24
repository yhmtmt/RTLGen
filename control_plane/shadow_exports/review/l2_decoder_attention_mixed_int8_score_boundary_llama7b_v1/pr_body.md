## Summary
- item_id: `l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1_run_235802f7765ff1b0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `48d3415f3b62bd1ffc58c7acc0b4f8c932b7e722`
- review_metadata_source_commit: `48d3415f3b62bd1ffc58c7acc0b4f8c932b7e722`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_score_boundary`
- comparison_role: `precision_boundary`
- expected_direction: `find_lowest_passing_score_precision`
- expected_reason: `The previous ablation showed QKV8 itself passes but score8 fails; the next frontier needs the lowest score precision that still preserves rankings.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_boundary__l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=12; weight_bits=8; softmax_mode=rtl_exact; comparison_count=16; top1_match_rate=0.5625; topk_contains_rate=0.75; mean_logit_cosine=0.9388521451215864; mean_probability_kl=0.988032547806978; max_abs_logit_delta_max=10.3984375; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=score10_float; best_top1_match_rate=0.6875; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9764499680089153; best_mean_probability_kl=0.4291034575331289; candidate_count=8.`

## Focused Comparison
- primary_question: `What is the lowest attention score precision that preserves native 7B-class checkpoint rankings for QKV8 attention?`
- comparison_role: `precision_boundary`
- proposal_outcome: `mixed_int8_native_attention_shadow_hold`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_boundary__l2_decoder_attention_mixed_int8_score_boundary_llama7b_v1.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=12; weight_bits=8; softmax_mode=rtl_exact; comparison_count=16; top1_match_rate=0.5625; topk_contains_rate=0.75; mean_logit_cosine=0.9388521451215864; mean_probability_kl=0.988032547806978; max_abs_logit_delta_max=10.3984375; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=score10_float; best_top1_match_rate=0.6875; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9764499680089153; best_mean_probability_kl=0.4291034575331289; candidate_count=8.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
