## Summary
- item_id: `l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1_run_b7d876d9d5232f84`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `74623af52e7cba8eeced36efbe5236906b9a0d3d`
- review_metadata_source_commit: `74623af52e7cba8eeced36efbe5236906b9a0d3d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence`
- comparison_role: `closure_detail`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence__l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What drain-time and congestion change appears when the complete Llama7B Phase-2 schedule is constrained by embodied endpoint control and checked against RTL?`
- comparison_role: `closure_detail`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence__l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
