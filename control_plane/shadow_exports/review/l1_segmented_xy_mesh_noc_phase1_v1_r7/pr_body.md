## Summary
- item_id: `l1_segmented_xy_mesh_noc_phase1_v1_r7`
- run_key: `l1_segmented_xy_mesh_noc_phase1_v1_r7_run_07e4261370b86503`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_segmented_xy_mesh_noc_phase1_v1_r7/evaluated.json`
- metrics_rows_count: `3`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_segmented_xy_mesh_noc_phase1_v1_r7.json`

## Developer Context
- proposal_id: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- proposal_path: `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b955da0ba0c7110f15b3fbed87f30dd857da2e8f`
- review_metadata_source_commit: `b955da0ba0c7110f15b3fbed87f30dd857da2e8f`

## Evaluation Mode
- evaluation_mode: `ppa`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
