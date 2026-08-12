## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2`
- run_key: `l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2_run_a9ecfec4f2868b61`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a9c5a0c5afd8e673dc1d423c172271ca1dcb8499`
- review_metadata_source_commit: `a9c5a0c5afd8e673dc1d423c172271ca1dcb8499`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost`
- comparison_role: `frontier_closure`
- expected_direction: `record_corrected_recost`
- expected_reason: `Use only merged corrected physical, functional, and workload dependencies and preserve conservative timing and energy provenance.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost__l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What four-point physical recost is obtained when every divider lane uses its matching temporal measurement and finalized-CDC probe at the selected 10 ns / 12 ns domain periods?`
- comparison_role: `frontier_closure`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost__l2_decoder_attention_decode_score_multivalue_service_exact_partial_physical_recost_10ns_12ns_v1_r2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
