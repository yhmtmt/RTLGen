## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1_run_ea802c27b4a377ee`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `39f44cf83e48565a4a9b26a751f70f0e6f066d53`
- review_metadata_source_commit: `d160e0c0cc5c37eb6d0cad47aa385584e05b0781`

## Evaluation Mode
- evaluation_mode: `equivalence`
- abstraction_layer: `decoder_attention_decode_score_multivalue_service_exact_partial_equivalence`
- comparison_role: `exact_partial_functional_validation`
- expected_direction: `record_exact_partial_shared_service_equivalence`
- expected_reason: `Require exact partial state through the shared service before any full-context temporal composition or frontier promotion.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_exact_partial_equivalence__l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=14472; max_service_penalty_cycles=13818; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=8488; selected_scale_point_service_penalty_cycles=7834; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.`

## Focused Comparison
- primary_question: `Does the shared multivalue service preserve exact global_max, exp_sum, head_id, slice/last, and all 8xS41 numerator lanes in exact_partial result mode?`
- comparison_role: `exact_partial_functional_validation`
- proposal_outcome: `multivalue_integrated_service_probe_passed`
- comparison_summary: `Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_exact_partial_equivalence__l2_decoder_attention_decode_score_multivalue_service_exact_partial_equivalence_llama7b_v1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=14472; max_service_penalty_cycles=13818; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=8488; selected_scale_point_service_penalty_cycles=7834; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
