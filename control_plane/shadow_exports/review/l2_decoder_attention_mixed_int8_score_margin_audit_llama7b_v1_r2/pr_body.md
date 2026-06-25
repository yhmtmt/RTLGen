## Summary
- item_id: `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2`
- run_key: `l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2_run_a39a4076a4a85acc`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e325e0b2ca3ab4c2da45d9e8a188638a9e7f8c33`
- review_metadata_source_commit: `e325e0b2ca3ab4c2da45d9e8a188638a9e7f8c33`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score_margin_audit`
- comparison_role: `score_margin_audit`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=score32_float; primary_comparison_count=64; primary_top1_miss_count=2; primary_top1_match_rate=0.96875; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=1.0; primary_miss_mean_reference_margin=0.125; primary_miss_mean_probability_kl=0.002996711308909919; primary_miss_mean_logit_cosine=0.9999012209502798; primary_miss_max_abs_logit_delta=0.34375; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.`

## Focused Comparison
- primary_question: `Are the remaining mixed/int8 score precision top1 failures narrow-margin, top-k-stable drift or systematic quality failures?`
- comparison_role: `score_margin_audit`
- proposal_outcome: `score_margin_audit_narrow_margin_hold`
- comparison_summary: `Decoder mixed/int8 score-margin audit recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score_margin_audit__l2_decoder_attention_mixed_int8_score_margin_audit_llama7b_v1_r2.json: decision=score_margin_audit_narrow_margin_hold; candidate_count=6; primary_candidate_id=score32_float; primary_comparison_count=64; primary_top1_miss_count=2; primary_top1_match_rate=0.96875; primary_topk_contains_rate=1.0; primary_miss_topk_contains_rate=1.0; primary_miss_mean_reference_margin=0.125; primary_miss_mean_probability_kl=0.002996711308909919; primary_miss_mean_logit_cosine=0.9999012209502798; primary_miss_max_abs_logit_delta=0.34375; next_step=The misses are concentrated in narrow-margin regions; keep this recovery path blocked until bounded top-k and follow-up scoring checks show stable high-margin behavior.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
