## Summary
- item_id: `l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1_run_f98c514043c1cafa`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `aee481ec8ebcf4cb07ee75b731ffdb48994c9aa2`
- review_metadata_source_commit: `aee481ec8ebcf4cb07ee75b731ffdb48994c9aa2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_int8_quality_energy_frontier`
- comparison_role: `quality_energy_frontier`
- expected_direction: `select_quality_backed_softmax_measurement`
- expected_reason: `qkv8_float_exact is quality-backed but not physically composed; score32/PWL rows have PPA but fail quality. This audit chooses the next measured wrapper direction.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 quality/energy frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_energy_frontier__l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json: decision=mixed_int8_quality_energy_frontier_composed_measurement_required; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; score32_top1_match_rate=0.984375; q24_pwl_top1_match_rate=0.96875; best_fp16_softmax_proxy_candidate_id=qkv8_float_exact_fp16_softmax_nm2_proxy; best_fp16_softmax_proxy_critical_path_ns=5.476841177082706; best_fp16_softmax_proxy_die_area_um2=2250000.0; best_fp16_softmax_proxy_total_power_mw=0.189074; non_quality_backed_measured_recost_count=2; recommended_next_step=Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.`

## Focused Comparison
- primary_question: `Which measured hardware evidence can safely support the quality-backed mixed/int8 Llama7B frontier after fixed-point/PWL softmax failed quality?`
- comparison_role: `quality_energy_frontier`
- proposal_outcome: `mixed_int8_quality_energy_frontier_composed_measurement_required`
- comparison_summary: `Decoder mixed/int8 quality/energy frontier evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_quality_energy_frontier__l2_decoder_attention_mixed_int8_quality_energy_frontier_llama7b_v1.json: decision=mixed_int8_quality_energy_frontier_composed_measurement_required; quality_best_candidate_id=qkv8_float_exact; quality_best_top1_match_rate=1.0; score32_top1_match_rate=0.984375; q24_pwl_top1_match_rate=0.96875; best_fp16_softmax_proxy_candidate_id=qkv8_float_exact_fp16_softmax_nm2_proxy; best_fp16_softmax_proxy_critical_path_ns=5.476841177082706; best_fp16_softmax_proxy_die_area_um2=2250000.0; best_fp16_softmax_proxy_total_power_mw=0.189074; non_quality_backed_measured_recost_count=2; recommended_next_step=Measure a composed q8/k8/v8 attention wrapper that keeps qkv8_float_exact quality semantics and substitutes a floating/near-exact softmax datapath; do not rank score32 exact-div or PWL rows as quality-backed frontier points.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
