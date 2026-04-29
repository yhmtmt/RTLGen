## Summary
- item_id: `l2_decoder_q8_normalization_frontier_v1`
- run_key: `l2_decoder_q8_normalization_frontier_v1_run_7e648ecf4b504ede`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_q8_normalization_frontier_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_q8_normalization_frontier_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_q8_normalization_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_q8_normalization_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_q8_normalization_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4fd31b3adb2926a88e088dee7a3fb6c20135eb2a`
- review_metadata_source_commit: `4fd31b3adb2926a88e088dee7a3fb6c20135eb2a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_q8_normalization_frontier`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Determine whether q8 reciprocal normalization can remove the exact-normalization blocker while preserving the prompt-stress quality gate.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Can q8 PWL reciprocal normalization at q10/q12/q14/q16 preserve the same prompt-stress quality as q8 exact normalization and the bf16 reciprocal anchor?`
- comparison_role: `ranking`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
