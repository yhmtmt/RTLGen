## Summary
- item_id: `l2_artifact_sync_submission_progress_confirm_v1`
- run_key: `l2_artifact_sync_submission_progress_confirm_v1_run_b6634f6bd4da0721`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `8/8 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_artifact_sync_submission_progress_confirm_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_artifact_sync_submission_progress_confirm_v1.json`

## Developer Context
- proposal_id: `prop_cp_artifact_sync_submission_progress_v1`
- proposal_path: `docs/proposals/prop_cp_artifact_sync_submission_progress_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_cp_artifact_sync_submission_progress_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8294a774e8c6145e497946277c4250675d9cf177`
- review_metadata_source_commit: `22f5c841552318026d8afe8da3a87c07a0db3a67`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `decoder_probability_path`
- comparison_role: `workflow_confirmation`
- expected_direction: `iterate`
- expected_reason: `Workflow confirmation only; resolver should remain quiet after submission progress events.`
- expectation_status: `not_applicable`
- evaluation_summary: `This item records metrics for the requested architecture point and does not emit a proposal judgment.`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_artifact_sync_submission_progress_confirm_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
