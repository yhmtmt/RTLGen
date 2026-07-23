## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_run_699edb450df4fb42`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1e3258cd16a33487c8b91a80964070470e1c5b87`
- review_metadata_source_commit: `1e3258cd16a33487c8b91a80964070470e1c5b87`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_decode_score_multivalue_integrated_service`
- comparison_role: `frontier_validation`
- expected_direction: `record_decode_score_multivalue_integrated_service_probe`
- expected_reason: `Retain exact Python/baseline/integrated hashes and protocol/count gates while recording finite service penalties and contention across the bounded 14-case matrix.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=21925; max_service_penalty_cycles=13591; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=15821; selected_scale_point_service_penalty_cycles=7487; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.`

## Focused Comparison
- primary_question: `Does the merged shared-score multivalue cluster retain exact result hashes and protocol/count gates once the integrated on-chip value service is exercised across a bounded scale/resource matrix through 32 clusters?`
- comparison_role: `frontier_validation`
- proposal_outcome: `multivalue_integrated_service_probe_passed`
- comparison_summary: `Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=21925; max_service_penalty_cycles=13591; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=15821; selected_scale_point_service_penalty_cycles=7487; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
