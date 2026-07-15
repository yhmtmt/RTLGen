## Summary
- item_id: `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2`
- run_key: `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2_run_cb65b821177b511e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `eaef7adde86bab3e3d0a0d7fba256aca2e9252ab`
- review_metadata_source_commit: `eaef7adde86bab3e3d0a0d7fba256aca2e9252ab`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_decode_score_local_cluster_frontier`
- comparison_role: `decode_composed_cluster_corrective_recost`
- expected_direction: `reprice_with_composed_cluster_lower_bound`
- expected_reason: `The corrected evidence must preserve the composed result while removing evaluator-local paths.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.`

## Focused Comparison
- primary_question: `How does the measured composed M1x8 score cluster change the precision-aligned Llama7B frontier once score storage, replay, division, and all 16 value slices per head are charged?`
- comparison_role: `decode_composed_cluster_corrective_recost`
- proposal_outcome: `prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only`
- comparison_summary: `Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
