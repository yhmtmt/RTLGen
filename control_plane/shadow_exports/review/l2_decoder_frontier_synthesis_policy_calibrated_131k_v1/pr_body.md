## Summary
- item_id: `l2_decoder_frontier_synthesis_policy_calibrated_131k_v1`
- run_key: `l2_decoder_frontier_synthesis_policy_calibrated_131k_v1_run_98fa4131fe9606e6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_frontier_synthesis_policy_calibrated_131k_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_frontier_synthesis_policy_calibrated_131k_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_frontier_synthesis_policy_calibrated_131k_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_131k_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_131k_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `aa66b8d6c7c5f40af91e8508016f581f2a4131df`
- review_metadata_source_commit: `aa66b8d6c7c5f40af91e8508016f581f2a4131df`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_frontier_synthesis_policy_calibrated`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use 131k attention/KV evidence to choose integrated attention memory hierarchy versus producer memory/cache next.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_131k_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Does 131k attention/KV overtake output-projection producer service in the matched calibrated frontier rows?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_131k_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
