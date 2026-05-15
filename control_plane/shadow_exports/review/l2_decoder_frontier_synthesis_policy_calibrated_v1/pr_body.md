## Summary
- item_id: `l2_decoder_frontier_synthesis_policy_calibrated_v1`
- run_key: `l2_decoder_frontier_synthesis_policy_calibrated_v1_run_e7b1546b3c68b1dc`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_frontier_synthesis_policy_calibrated_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_frontier_synthesis_policy_calibrated_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_frontier_synthesis_policy_calibrated_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e9ba62507e2b4c072202c662b2abe51189a61c14`
- review_metadata_source_commit: `e9ba62507e2b4c072202c662b2abe51189a61c14`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_frontier_synthesis_policy_calibrated`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If output projection still dominates after calibrated ranker service, target producer memory/cache hierarchy; otherwise move to the newly dominant decoder component.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `After substituting calibrated producer/ranker latency, what component dominates the focused whole-decoder rows?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
