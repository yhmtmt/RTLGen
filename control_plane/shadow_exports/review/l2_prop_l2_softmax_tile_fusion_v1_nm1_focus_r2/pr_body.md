## Summary
- item_id: `l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2`
- run_key: `l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2_run_e87c163f8d1017aa`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_softmax_tile_fusion_v1_nm1_focus_r2.json`

## Developer Context
- proposal_id: `prop_l2_softmax_tile_fusion_v1`
- proposal_path: `docs/developer_loop/prop_l2_softmax_tile_fusion_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_softmax_tile_fusion_v1` plus `docs/developer_agent_review.md`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
