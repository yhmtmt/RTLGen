## Summary
- item_id: `l1_prop_l1_terminal_hardsigmoid_retrysubmission_v1_nangate45_r2`
- run_key: `l1_prop_l1_terminal_hardsigmoid_retrysubmission_v1_nangate45_r2_run_4133f9132c217a1f`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_prop_l1_terminal_hardsigmoid_retrysubmission_v1_nangate45_r2/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_prop_l1_terminal_hardsigmoid_retrysubmission_v1_nangate45_r2.json`

## Developer Context
- proposal_id: `prop_l1_terminal_hardsigmoid_retrysubmission_v1`
- proposal_path: `docs/proposals/prop_l1_terminal_hardsigmoid_retrysubmission_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_terminal_hardsigmoid_retrysubmission_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `circuit_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Submission Recovery
- resolver_retry_path: `true`
- submission_failure_count: `2`
- retry_request_count: `3`
- last_submission_failure: `gh pr create failed: gh auth login required`
- retry_request_id: `resume_135a90c2d9d29c31`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/194`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
