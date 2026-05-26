## Summary
- item_id: `l1_npu_corrected_compute_frontier_nm64_v1`
- run_key: `l1_npu_corrected_compute_frontier_nm64_v1_run_8133ff1f5f4b0bea`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_corrected_compute_frontier_nm64_v1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_corrected_compute_frontier_nm64_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_corrected_compute_nm64_boundary_v1`
- proposal_path: `docs/proposals/prop_l1_npu_corrected_compute_nm64_boundary_v1`
- reviewer_first_read: `docs/proposals/prop_l1_npu_corrected_compute_nm64_boundary_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `fe40b20ef8ee49e1ed9e24389bb833e8810458b5`
- review_metadata_source_commit: `fe40b20ef8ee49e1ed9e24389bb833e8810458b5`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_corrected_compute_nm64_boundary`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
