## Summary
- item_id: `l1_daemon_real_ingest_r4_acc20_20260311134953`
- run_key: `l1_daemon_real_ingest_r4_acc20_20260311134953_run_93e6f5608d256e55`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_daemon_real_ingest_r4_acc20_20260311134953/evaluated.json`
- metrics_rows_count: `8`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_daemon_real_ingest_r4_acc20_20260311134953.json`

## Checklist
- [ ] Commit only lightweight metrics and regenerated runs/index.csv
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
