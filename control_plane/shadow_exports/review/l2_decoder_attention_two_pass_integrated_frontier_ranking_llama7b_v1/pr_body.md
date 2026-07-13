## Summary
- item_id: `l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1`
- run_key: `l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1_run_a86475c4007d07df`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8f41146c030f8f3324eac52250932983a5ff75f9`
- review_metadata_source_commit: `fc4b505619c9f02354e895e35fb3563ecfc07eb5`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_two_pass_integrated_frontier_ranking`
- comparison_role: `measured_two_pass_frontier_ranking`
- expected_direction: `rank_measured_two_pass_deployments`
- expected_reason: `Charge measured divider, score SRAM, and zero-tail quality together while preserving controller replay.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder two-pass integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_integrated_frontier_ranking__l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1.json: decision=two_pass_measured_components_integrated_frontier_ranked; recommended_candidate=score32_zero_tail_two_pass_nominal_per_head_iterdiv; recommended_latency_us=12940.224364999998; recommended_token_throughput_per_s=77.278412784306; minimum_area_candidate=score32_zero_tail_two_pass_nominal_shared_iterdiv; shared_divider_latency_penalty_us=148.8; per_head_divider_area_premium_mm2=3.531551; quality_status=mixed_int8_generation_quality_pass; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr'].`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `measured_two_pass_frontier_ranking`
- proposal_outcome: `two_pass_measured_components_integrated_frontier_ranked`
- comparison_summary: `Decoder two-pass integrated frontier ranking recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_integrated_frontier_ranking__l2_decoder_attention_two_pass_integrated_frontier_ranking_llama7b_v1.json: decision=two_pass_measured_components_integrated_frontier_ranked; recommended_candidate=score32_zero_tail_two_pass_nominal_per_head_iterdiv; recommended_latency_us=12940.224364999998; recommended_token_throughput_per_s=77.278412784306; minimum_area_candidate=score32_zero_tail_two_pass_nominal_shared_iterdiv; shared_divider_latency_penalty_us=148.8; per_head_divider_area_premium_mm2=3.531551; quality_status=mixed_int8_generation_quality_pass; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- resolver_retry_path: `true`
- submission_failure_count: `0`
- retry_request_count: `1`
- retry_request_id: `resume_79269440654f13db`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
