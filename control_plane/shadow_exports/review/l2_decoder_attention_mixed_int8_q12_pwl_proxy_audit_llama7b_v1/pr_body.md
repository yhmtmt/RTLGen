## Summary
- item_id: `l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1_run_6d8b014f4068f1d0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `fc78bdce1b0901c66e6be30c9e142402fe57f6b1`
- review_metadata_source_commit: `5f7bf627854bd3a983a1346d0e66e78bb86b4b3e`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_q12_pwl_proxy_audit`
- comparison_role: `quality_backed_proxy`
- expected_direction: `validate_or_recost_q12_pwl_proxy`
- expected_reason: `Use measured q12/PWL PPA only if quality passes; otherwise require v8 composed recost or reject the proxy.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 q12/PWL proxy audit evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q12_pwl_proxy_audit__l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json: decision=q12_pwl_proxy_quality_rejected; q12_candidate_id=qkv8_q12_pwl_recip_q12_bucket8; q12_decision_status=mixed_int8_native_attention_shadow_hold; q12_top1_match_rate=0.96875; q12_topk_contains_rate=1.0; q12_mean_probability_kl=0.014237412876954065; q12_quality_passed=False; q12_proxy_pass=False; composed_metrics_path=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv; composed_value_bits=6; composed_best_critical_path_ns=30.8676; composed_best_total_power_mw=23.7; composed_best_die_area_um2=6250000.0; v8_full_value_metrics_path=runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv; v8_full_value_best_critical_path_ns=0.8825; v8_full_value_best_total_power_mw=0.0339; v8_full_value_best_die_area_um2=130100.883025; recommended_next_step=Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.`

## Focused Comparison
- primary_question: `Can the measured q12/PWL composed softmax datapath be used as a quality-backed proxy for the qkv8_float_exact frontier, or must the v8 composed datapath be measured first?`
- comparison_role: `quality_backed_proxy`
- proposal_outcome: `q12_pwl_proxy_quality_rejected`
- comparison_summary: `Decoder mixed/int8 q12/PWL proxy audit evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_q12_pwl_proxy_audit__l2_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1.json: decision=q12_pwl_proxy_quality_rejected; q12_candidate_id=qkv8_q12_pwl_recip_q12_bucket8; q12_decision_status=mixed_int8_native_attention_shadow_hold; q12_top1_match_rate=0.96875; q12_topk_contains_rate=1.0; q12_mean_probability_kl=0.014237412876954065; q12_quality_passed=False; q12_proxy_pass=False; composed_metrics_path=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/metrics.csv; composed_value_bits=6; composed_best_critical_path_ns=30.8676; composed_best_total_power_mw=23.7; composed_best_die_area_um2=6250000.0; v8_full_value_metrics_path=runs/designs/activations/attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper/metrics.csv; v8_full_value_best_critical_path_ns=0.8825; v8_full_value_best_total_power_mw=0.0339; v8_full_value_best_die_area_um2=130100.883025; recommended_next_step=Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/1017`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
