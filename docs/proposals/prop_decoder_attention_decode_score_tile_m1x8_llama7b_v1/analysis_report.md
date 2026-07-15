# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2`

## Evaluations Consumed
- `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2`
- `l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2_run_cb65b821177b511e`
- source commit: `eaef7adde86bab3e3d0a0d7fba256aca2e9252ab`
- review: PR #1314

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only`
- summary: Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder composed score-cluster frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_frontier__l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2.json: decision=prior_decode_score_tile_frontier_retracted_composed_cluster_lower_bound_only; prior_best_token_throughput_per_s_retracted=669.792507491203; best_no_stall_candidate=decode_score_local_cluster_c128_vl1; best_no_stall_token_throughput_upper_bound_per_s=0.521229054458; best_no_stall_latency_lower_bound_us=1918542.321168; best_no_stall_area_mm2=634.909914937; promotion_blocked=True; next_architecture=Split the QK producer/score bank from replicated value-slice accumulators so one score fill and replay stream serves all 16 value slices; then measure composed routing and activity.
- next_action: inspect follow-on work after l2_decoder_attention_decode_score_local_cluster_frontier_llama7b_v2
