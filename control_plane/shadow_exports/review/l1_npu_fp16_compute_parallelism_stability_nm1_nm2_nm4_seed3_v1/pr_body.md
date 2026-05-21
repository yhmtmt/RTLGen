## Summary
- item_id: `l1_npu_fp16_compute_parallelism_stability_nm1_nm2_nm4_seed3_v1`
- run_key: `l1_npu_fp16_compute_parallelism_stability_nm1_nm2_nm4_seed3_v1_run_5dbcdd8553bd2ace`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `1/3 seed trials succeeded; 2 trial failures recorded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_fp16_compute_parallelism_stability_nm1_nm2_nm4_seed3_v1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_fp16_compute_parallelism_stability_nm1_nm2_nm4_seed3_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_fp16_compute_parallelism_stability_v1`
- proposal_path: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_stability_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_stability_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `7f343c3aa1b1f1bcaf7ecdb78f89795467958573`
- review_metadata_source_commit: `37f798bec3b5e27100cc8ee4cd888e097013a97d`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_compute_parallelism_stability`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l1_npu_fp16_compute_parallelism_stability_nm1_nm2_nm4_seed3_v1 is not eligible for submission: proposal already finalized with decision=promote`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
