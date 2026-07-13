## Summary
- item_id: `l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1`
- run_key: `l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1_run_b95116cc4c39841a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `275673eb674626455a988b848941edbf28fd02cd`
- review_metadata_source_commit: `98812adafb0c9fa81aaf526f38ed790ed84cdf52`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_two_pass_score_sram_reservation`
- comparison_role: `measured_score_memory_recost`
- expected_direction: `reserve_measured_score_sram_before_kv`
- expected_reason: `The two-pass score store must consume concrete SRAM area, ports, and energy instead of borrowing the full shared-KV capacity envelope.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_changes_frontier; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=29.015625; nominal_hbm_byte_share=0.992916107; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=16.265625; conservative_hbm_byte_share=0.9960289; conservative_hbm_share_delta=0.012630462; conservative_projected_latency_us_hbm_share_scaled=12680.136872; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `measured_score_memory_recost`
- proposal_outcome: `score32_exp_lut_sram_hierarchy_envelope_changes_frontier`
- comparison_summary: `Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_changes_frontier; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=29.015625; nominal_hbm_byte_share=0.992916107; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=16.265625; conservative_hbm_byte_share=0.9960289; conservative_hbm_share_delta=0.012630462; conservative_projected_latency_us_hbm_share_scaled=12680.136872; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- resolver_retry_path: `true`
- submission_failure_count: `1`
- retry_request_count: `1`
- last_submission_failure: `work item l2_decoder_attention_two_pass_score_sram_reservation_llama7b_v1 is not eligible for submission: proposal already finalized with decision=promote`
- retry_request_id: `resume_8845fde13a7f0626`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
