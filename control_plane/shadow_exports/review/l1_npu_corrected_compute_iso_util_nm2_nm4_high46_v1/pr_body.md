## Summary
- item_id: `l1_npu_corrected_compute_iso_util_nm2_nm4_high46_v1`
- run_key: `l1_npu_corrected_compute_iso_util_nm2_nm4_high46_v1_run_57cb8f990a60b898`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_corrected_compute_iso_util_nm2_nm4_high46_v1/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_corrected_compute_iso_util_nm2_nm4_high46_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_corrected_compute_iso_util_v1`
- proposal_path: `docs/proposals/prop_l1_npu_corrected_compute_iso_util_v1`
- reviewer_first_read: `docs/proposals/prop_l1_npu_corrected_compute_iso_util_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `db7669bf57e1f032f354a778b4f3b4a84d077d12`
- review_metadata_source_commit: `db7669bf57e1f032f354a778b4f3b4a84d077d12`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_corrected_compute_iso_util`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
