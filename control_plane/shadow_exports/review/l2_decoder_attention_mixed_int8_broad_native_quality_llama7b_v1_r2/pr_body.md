## Summary
- item_id: `l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2`
- run_key: `l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2_run_a756884b923d650b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `47e6974fc6ffae2e10e5b491bf968a2d5106bfa7`
- review_metadata_source_commit: `47e6974fc6ffae2e10e5b491bf968a2d5106bfa7`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_broad_native_quality`
- comparison_role: `precision_validation`
- expected_direction: `validate_score24_float_before_ppa`
- expected_reason: `The first broad-native-quality run completed but mixed/int8 dataset outputs were not transported; after fixing artifact transport, rerun the same score24_float quality gate before PPA is spent on the score24 mixed/int8 point.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.`

## Focused Comparison
- primary_question: `Does the score24 QKV8 attention-shadow point still preserve native 7B-class checkpoint rankings on a broader prompt set?`
- comparison_role: `precision_validation`
- proposal_outcome: `mixed_int8_native_attention_shadow_hold`
- comparison_summary: `Decoder mixed/int8 native attention quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_broad_native_quality__l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1_r2.json: decision=mixed_int8_native_attention_shadow_hold; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; q_bits=8; k_bits=8; v_bits=8; score_bits=24; weight_bits=16; softmax_mode=float_quantized; comparison_count=64; top1_match_rate=0.96875; topk_contains_rate=1.0; mean_logit_cosine=0.9999025562684435; mean_probability_kl=0.0014115558838723183; max_abs_logit_delta_max=0.53125; next_step=Hold this attention-shadow candidate until safer quantization is proven with a real checkpoint run or broader model sampling.; best_candidate_id=qkv8_float_exact; best_top1_match_rate=1.0; best_topk_contains_rate=1.0; best_mean_logit_cosine=0.9998988400355315; best_mean_probability_kl=0.0012425925766148221; candidate_count=4.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
