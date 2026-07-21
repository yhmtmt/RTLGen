## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12`
- run_key: `l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12_run_1dedc7e2b655a68c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `b84e932f563008ae382c1c5b64d9fc109abd50c9`
- review_metadata_source_commit: `ae41a5797e0f28fb5e17f8bdeed4a12a7182d2b9`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster_activity_power`
- comparison_role: `shared_score_multivalue_cluster_activity_power_gate`
- expected_direction: `record_shared_score_multivalue_cluster_activity_power_gate`
- expected_reason: `v12 preserves the existing quality/equivalence/direct-VCD/macro/clock/numeric/artifact gates, requires >=0.95 DFF-output coverage, applied==matched, and zero query/apply errors, keeps sidecar rows evaluator-local, and forbids clamping, substitution, heuristic activity, and gate relaxation.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder multivalue-cluster activity-power evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_cluster_activity_power__l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12.json: decision=activity_power_rejected_no_gated_candidate; promotion_gate_pass=False; candidate_count=1; promoted_candidate_count=0; best_candidate_id=None; representative_candidate_id=multivalue_cluster_activity_decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500; representative_flow_variant=decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500; representative_status=measurement_failed; representative_ppa_critical_path_ns=7.1765; representative_ppa_instance_area_um2=2785000.0; representative_ppa_total_power_mw=0.348.`

## Focused Comparison
- primary_question: `Does the shared-score multivalue cluster remain physically interesting once evaluator-local activity evidence replaces the current vectorless-power placeholder?`
- comparison_role: `shared_score_multivalue_cluster_activity_power_gate`
- proposal_outcome: `activity_power_rejected_no_gated_candidate`
- comparison_summary: `Decoder multivalue-cluster activity-power evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_cluster_activity_power__l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v12.json: decision=activity_power_rejected_no_gated_candidate; promotion_gate_pass=False; candidate_count=1; promoted_candidate_count=0; best_candidate_id=None; representative_candidate_id=multivalue_cluster_activity_decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500; representative_flow_variant=decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500; representative_status=measurement_failed; representative_ppa_critical_path_ns=7.1765; representative_ppa_instance_area_um2=2785000.0; representative_ppa_total_power_mw=0.348.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
