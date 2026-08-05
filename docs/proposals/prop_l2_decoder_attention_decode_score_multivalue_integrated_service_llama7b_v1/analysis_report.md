# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1`

## Evaluations Consumed
- `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1`
- `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1_run_d782775c592cba54`
- source commit: `b1451ded32b9dcaa800ed63b886c73a917ba2cb4`
- review: PR #1539

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `multivalue_integrated_service_probe_passed`
- summary: Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=21925; max_service_penalty_cycles=13591; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=15821; selected_scale_point_service_penalty_cycles=7487; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=21925; max_service_penalty_cycles=13591; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=15821; selected_scale_point_service_penalty_cycles=7487; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder multivalue integrated-service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1.json: decision=multivalue_integrated_service_probe_passed; validated_case_count=14; max_cluster_count=32; max_completion_cycle=21925; max_service_penalty_cycles=13591; stress_case_id=c32_p256_b32_rl6_rr; all_hash_gates_passed=True; all_protocol_gates_passed=True; all_count_gates_passed=True; selected_scale_point_selection_role=representative_largest_nominal_scale_point; selected_scale_point_case_id=c32_p256_b32_rr; selected_scale_point_completion_cycle=15821; selected_scale_point_service_penalty_cycles=7487; selected_scale_point_shared_result_egress_block_cycles=6; selected_scale_point_router_arbitration_contention_cycles=7606; selected_scale_point_bank_conflict_count=1533; recommended_next_step=Use this merged/materialized integrated-service probe as the shared-score on-chip service closure input before any NoC, HBM, physical PPA, SRAM macro timing, or token-energy claim.
- next_action: inspect follow-on work after l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1_r1
