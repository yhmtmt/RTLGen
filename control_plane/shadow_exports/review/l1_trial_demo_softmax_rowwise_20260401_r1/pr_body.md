## Summary
- item_id: `l1_trial_demo_softmax_rowwise_20260401_r1`
- run_key: `l1_trial_demo_softmax_rowwise_20260401_r1_run_e5c9a73cb1a3e582`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_trial_demo_softmax_rowwise_20260401_r1/evaluated.json`
- metrics_rows_count: `8`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_trial_demo_softmax_rowwise_20260401_r1.json`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `circuit_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics and regenerated runs/index.csv
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
