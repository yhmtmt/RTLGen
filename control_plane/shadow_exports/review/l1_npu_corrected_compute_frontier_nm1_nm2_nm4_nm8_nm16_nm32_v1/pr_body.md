## Summary
- item_id: `l1_npu_corrected_compute_frontier_nm1_nm2_nm4_nm8_nm16_nm32_v1`
- run_key: `l1_npu_corrected_compute_frontier_nm1_nm2_nm4_nm8_nm16_nm32_v1_run_29e8b9360873c7e7`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `15/15 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_corrected_compute_frontier_nm1_nm2_nm4_nm8_nm16_nm32_v1/evaluated.json`
- metrics_rows_count: `44`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_corrected_compute_frontier_nm1_nm2_nm4_nm8_nm16_nm32_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_corrected_compute_frontier_v1`
- proposal_path: `docs/proposals/prop_l1_npu_corrected_compute_frontier_v1`
- reviewer_first_read: `docs/proposals/prop_l1_npu_corrected_compute_frontier_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `25569a671d556632df11e7170d7da4e4b876f0e6`
- review_metadata_source_commit: `25569a671d556632df11e7170d7da4e4b876f0e6`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_corrected_compute_frontier`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
