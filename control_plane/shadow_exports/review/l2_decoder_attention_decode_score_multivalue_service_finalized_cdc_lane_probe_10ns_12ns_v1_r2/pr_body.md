## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2`
- run_key: `l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2_run_3391b033de14da8a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8305ec1b4c066aea15830a701784fe2f9bfe3914`
- review_metadata_source_commit: `8305ec1b4c066aea15830a701784fe2f9bfe3914`

## Evaluation Mode
- evaluation_mode: `equivalence`
- abstraction_layer: `decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe`
- comparison_role: `functional_prerequisite`
- expected_direction: `pass`
- expected_reason: `All lane outputs and counters should remain exact while directed backpressure guarantees stability coverage independent of lane timing.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe__l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2/campaign_summary.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Do all four divider-lane variants preserve finalized exact-partial functional behavior at service_period_ns=10 and temporal_period_ns=12 with the physical-memory backends enabled, and what elapsed service/temporal cycle counts do they report?`
- comparison_role: `functional_prerequisite`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe__l2_decoder_attention_decode_score_multivalue_service_finalized_cdc_lane_probe_10ns_12ns_v1_r2/campaign_summary.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
