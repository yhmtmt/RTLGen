## Summary
- item_id: `l1_segmented_xy_mesh_noc_phase1_v1_r6`
- run_key: `l1_segmented_xy_mesh_noc_phase1_v1_r6_run_fbe5773fc9610529`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_segmented_xy_mesh_noc_phase1_v1_r6/evaluated.json`
- metrics_rows_count: `3`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_segmented_xy_mesh_noc_phase1_v1_r6.json`

## Developer Context
- proposal_id: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- proposal_path: `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ed1ddb403a3249e33a4f74ab466b28a2d3544a44`
- review_metadata_source_commit: `ed1ddb403a3249e33a4f74ab466b28a2d3544a44`

## Evaluation Mode
- evaluation_mode: `ppa`
- abstraction_layer: `architecture_block`
- evaluation_summary: `No timing-feasible Layer 1 rows were produced; completed flows that miss their declared clock period are retained as explicit timing-boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All completed physical rows miss their declared clock period; retain them as timing-boundary evidence and do not promote a feasible design point.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
