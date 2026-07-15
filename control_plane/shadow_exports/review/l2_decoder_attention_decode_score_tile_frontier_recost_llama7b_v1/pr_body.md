## Summary
- item_id: `l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1_run_341202d7fe3e5639`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `2613af1091ac00621b505ba27ab7e231da2cbd5e`
- review_metadata_source_commit: `2613af1091ac00621b505ba27ab7e231da2cbd5e`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_decode_score_tile_frontier`
- comparison_role: `decode_shape_corrective_recost`
- expected_direction: `reprice_frontier_with_decode_exact_compute_shape`
- expected_reason: `The active Llama7B decision path must recompute stage service instead of scaling an M16 tile as if all rows were useful during M1 decode.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder M1x8 score-tile frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_tile_frontier__l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1.json: decision=decode_shaped_m1x8_schedule_and_area_recosted_energy_retained; best_throughput_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_scalar_area_budget; best_throughput_token_per_s=669.792507491203; best_throughput_area_mm2=482.5046840209; best_area_candidate=score32_separated_zero_tail_two_pass_nominal_shared_iterdiv_operational_components_decode_m1x8_scalar_nominal_peak; best_area_mm2=323.4220925409; best_area_token_per_s=570.666388631788; energy_promotion_blocked=True; next_step=physically compose one selected M1x8 tile, score bank, and two-pass service cluster with activity.`

## Focused Comparison
- primary_question: `How do scalar-drain and packed-row M1x8 score tiles change measured area, delay, and the precision-aligned Llama7B token frontier relative to the semantically mismatched M16x8 recost?`
- comparison_role: `decode_shape_corrective_recost`
- proposal_outcome: `decode_shaped_m1x8_schedule_and_area_recosted_energy_retained`
- comparison_summary: `Decoder M1x8 score-tile frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_tile_frontier__l2_decoder_attention_decode_score_tile_frontier_recost_llama7b_v1.json: decision=decode_shaped_m1x8_schedule_and_area_recosted_energy_retained; best_throughput_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_scalar_area_budget; best_throughput_token_per_s=669.792507491203; best_throughput_area_mm2=482.5046840209; best_area_candidate=score32_separated_zero_tail_two_pass_nominal_shared_iterdiv_operational_components_decode_m1x8_scalar_nominal_peak; best_area_mm2=323.4220925409; best_area_token_per_s=570.666388631788; energy_promotion_blocked=True; next_step=physically compose one selected M1x8 tile, score bank, and two-pass service cluster with activity.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
