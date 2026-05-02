## Summary
- item_id: `l2_decoder_pwl_logit_ladder_v1`
- run_key: `l2_decoder_pwl_logit_ladder_v1_run_ff6ff5fe98dc4293`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pwl_logit_ladder_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pwl_logit_ladder_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pwl_logit_ladder_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pwl_logit_ladder_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pwl_logit_ladder_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `75cda3daf1705e0ed7abe196649431103beef386`
- review_metadata_source_commit: `75cda3daf1705e0ed7abe196649431103beef386`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_pwl_logit_sensitivity_ladder`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Identify whether q8/bf16 precision, unquantized PWL approximation, or normalization precision explains the focused exact-token flips.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `On the two broad-v2 shared exact-token misses and nearby controls, which precision boundary first recovers exact next-token behavior while retaining top-k?`
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
