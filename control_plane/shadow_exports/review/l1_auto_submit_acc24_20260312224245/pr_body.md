## Summary
- item_id: `l1_auto_submit_acc24_20260312224245`
- run_key: `l1_auto_submit_acc24_20260312224245_run_41128dbb9b4b212c`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `heartbeat_error=(psycopg.OperationalError) consuming input failed: could not receive data from server: No route to host
SSL SYSCALL error: No route to host
[SQL: SELECT worker_leases.id AS worker_leases_id, worker_leases.work_item_id AS worker_leases_work_item_id, worker_leases.machine_id AS worker_leases_machine_id, worker_leases.lease_token AS worker_leases_lease_token, worker_leases.status AS worker_leases_status, worker_leases.leased_at AS worker_leases_leased_at, worker_leases.expires_at AS worker_leases_expires_at, worker_leases.last_heartbeat_at AS worker_leases_last_heartbeat_at 
FROM worker_leases 
WHERE worker_leases.lease_token = %(lease_token_1)s::VARCHAR]
[parameters: {'lease_token_1': 'lease_7976e67ca0da73d4'}]
(Background on this error at: https://sqlalche.me/e/20/e3q8)`
- queue_snapshot: `control_plane/shadow_exports/review/l1_auto_submit_acc24_20260312224245/evaluated.json`
- metrics_rows_count: `8`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_auto_submit_acc24_20260312224245.json`

## Checklist
- [ ] Commit only lightweight metrics and regenerated runs/index.csv
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
