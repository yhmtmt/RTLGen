## Summary
- item_id: `l1_prop_l1_terminal_relu6_block_v1_nangate45_r2`
- run_key: `l1_prop_l1_terminal_relu6_block_v1_nangate45_r2_run_0529d84d968268c3`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_prop_l1_terminal_relu6_block_v1_nangate45_r2/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_prop_l1_terminal_relu6_block_v1_nangate45_r2.json`

## Developer Context
- proposal_id: `prop_l1_terminal_relu6_block_v1`
- proposal_path: `docs/developer_loop/prop_l1_terminal_relu6_block_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_l1_terminal_relu6_block_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics and regenerated runs/index.csv
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
