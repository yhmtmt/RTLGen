## Summary
- item_id: `l2_decoder_generator_auto_evidence_confirm_v1`
- run_key: `l2_decoder_generator_auto_evidence_confirm_v1_run_8d63dfcfcf43f34b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `9/9 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_generator_auto_evidence_confirm_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_generator_auto_evidence_confirm_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_exact_probability_path_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_exact_probability_path_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_exact_probability_path_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4d7441890679ee9163781c36ca5b2b121a46cc63`
- review_metadata_source_commit: `4d7441890679ee9163781c36ca5b2b121a46cc63`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `decoder_probability_path`
- comparison_role: `measurement_only`
- expected_direction: `confirmation_only`
- expected_reason: `This job confirms PR #234 makes decoder evidence commands part of generation before dispatch.`
- expectation_status: `not_applicable`
- evaluation_summary: `This item records metrics for the requested architecture point and does not emit a proposal judgment.`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
