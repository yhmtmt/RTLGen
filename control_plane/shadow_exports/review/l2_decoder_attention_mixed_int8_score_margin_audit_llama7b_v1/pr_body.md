## Summary
- item_id: `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_run_fc4aaf9171ea2d3c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b4399701829e9b5c251ddcabd36cbc26c193e74a`
- review_metadata_source_commit: `b4399701829e9b5c251ddcabd36cbc26c193e74a`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score_margin_audit`
- comparison_role: `score_margin_audit`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=qkv8_float_exact; primary_comparison_count=64; primary_top1_miss_count=0; primary_top1_match_rate=1.0; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=0.0; primary_miss_mean_reference_margin=0.0; primary_miss_mean_probability_kl=0.0; primary_miss_mean_logit_cosine=0.0; primary_miss_max_abs_logit_delta=0.0; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.`

## Focused Comparison
- primary_question: `Are the remaining mixed/int8 score precision top1 failures narrow-margin, top-k-stable drift or systematic quality failures?`
- comparison_role: `score_margin_audit`
- proposal_outcome: `score_margin_audit_narrow_margin_hold`
- comparison_summary: `Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=qkv8_float_exact; primary_comparison_count=64; primary_top1_miss_count=0; primary_top1_match_rate=1.0; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=0.0; primary_miss_mean_reference_margin=0.0; primary_miss_mean_probability_kl=0.0; primary_miss_mean_logit_cosine=0.0; primary_miss_max_abs_logit_delta=0.0; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
