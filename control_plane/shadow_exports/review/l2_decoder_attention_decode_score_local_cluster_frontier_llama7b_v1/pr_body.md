## Summary
- item_id: `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1_run_5c08a682c6127815`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `d82715fe37862b33c273622ec18aa833225e376a`
- review_metadata_source_commit: `93410ed38653e08c96da68ccf57b806990d8a2fd`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_decode_score_local_cluster_frontier`
- comparison_role: `decode_composed_cluster_corrective_recost`
- expected_direction: `reprice_with_composed_cluster_lower_bound`
- expected_reason: `The active frontier must charge the measured 512 KiB score bank and all 16 eight-dimensional value slices per head.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.`

## Focused Comparison
- primary_question: `How do scalar-drain and packed-row M1x8 score tiles change measured area, delay, and the precision-aligned Llama7B token frontier relative to the semantically mismatched M16x8 recost?`
- comparison_role: `decode_composed_cluster_corrective_recost`
- proposal_outcome: `prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only`
- comparison_summary: `Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v1.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
