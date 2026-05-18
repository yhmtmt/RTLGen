## Summary
- item_id: `l1_npu_fp16_compute_parallelism_ladder_nm16_v1`
- run_key: `l1_npu_fp16_compute_parallelism_ladder_nm16_v1_run_6907e5f9af3875ad`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_fp16_compute_parallelism_ladder_nm16_v1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_fp16_compute_parallelism_ladder_nm16_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_fp16_compute_parallelism_ladder_v1`
- proposal_path: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_ladder_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_ladder_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1608a322e039cf85a8127a22b25a39866a00ecf9`
- review_metadata_source_commit: `1608a322e039cf85a8127a22b25a39866a00ecf9`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_compute_parallelism_ladder`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l1_npu_fp16_compute_parallelism_ladder_nm16_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
