## Summary
- item_id: `l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1`
- run_key: `l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1_run_810b03f72892a7d1`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b0a25aa1556a106e9fcb1484b6de2c08aeb09a47`
- review_metadata_source_commit: `b0a25aa1556a106e9fcb1484b6de2c08aeb09a47`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_frontier_synthesis_policy_calibrated`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use current broad attention/KV and large-array stage evidence to choose producer-memory vs attention-memory next measured block.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `With calibrated producer/ranker service and broad attention/KV evidence, which decoder component dominates the focused frontier rows?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_frontier_synthesis__l2_decoder_frontier_synthesis_policy_calibrated_broad_attention_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
