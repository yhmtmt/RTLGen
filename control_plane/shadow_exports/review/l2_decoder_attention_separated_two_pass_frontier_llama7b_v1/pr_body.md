## Summary
- item_id: `l2_decoder_attention_separated_two_pass_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_separated_two_pass_frontier_llama7b_v1_run_b59d1d137ebcc072`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_separated_two_pass_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_separated_two_pass_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `de542f5067d64273b0c110faf5945f04ae43c092`
- review_metadata_source_commit: `de542f5067d64273b0c110faf5945f04ae43c092`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_separated_two_pass_frontier`
- comparison_role: `precision_aligned_separated_two_pass_frontier`
- expected_direction: `rank_precision_aligned_separated_two_pass_frontier`
- expected_reason: `Transfer measured score-SRAM HBM-share deltas into the dense-producer baseline and replace the old local softmax component.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder separated-producer two-pass frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_two_pass_frontier__l2_decoder_attention_separated_two_pass_frontier_llama7b_v1.json: decision=score32_separated_two_pass_frontier_ranked; recommended_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv; recommended_latency_us=1595.42090302109; recommended_token_throughput_per_s=626.793843622331; recommended_total_energy_mj_per_token=137.330868813197; recommended_embodied_area_mm2=249.4256151009; minimum_area_candidate=score32_separated_zero_tail_two_pass_nominal_shared_iterdiv; quality_status=mixed_int8_generation_quality_pass; precision_status=mixed_int8_generation_quality_pass; remaining_abstractions=['score32_separated_compute_schedule_inheritance', 'hbm_dram_service', 'sram_macro_floorplan_pnr'].`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `precision_aligned_separated_two_pass_frontier`
- proposal_outcome: `score32_separated_two_pass_frontier_ranked`
- comparison_summary: `Decoder separated-producer two-pass frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_two_pass_frontier__l2_decoder_attention_separated_two_pass_frontier_llama7b_v1.json: decision=score32_separated_two_pass_frontier_ranked; recommended_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv; recommended_latency_us=1595.42090302109; recommended_token_throughput_per_s=626.793843622331; recommended_total_energy_mj_per_token=137.330868813197; recommended_embodied_area_mm2=249.4256151009; minimum_area_candidate=score32_separated_zero_tail_two_pass_nominal_shared_iterdiv; quality_status=mixed_int8_generation_quality_pass; precision_status=mixed_int8_generation_quality_pass; remaining_abstractions=['score32_separated_compute_schedule_inheritance', 'hbm_dram_service', 'sram_macro_floorplan_pnr'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
