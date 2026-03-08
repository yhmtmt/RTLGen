# RTLGen Control Plane

This subtree hosts the host-side control-plane implementation for RTLGen.

Phase 1 scope:
- import current Git queue items into a DB-backed operational state model,
- lease internal work to deterministic workers,
- export queue-compatible snapshots,
- preserve Git and PRs as the evidence boundary.

Current status:
- `cp-001` through `cp-007` are implemented in the initial shadow-control slice
- in-process API routing, queue import/export, leases, runs, and GitHub reconciliation exist
- Alembic files and the initial migration exist, but Alembic CLI still needs a clean dedicated env for live migration verification

## Local bring-up

Import check:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane python3 -c "from control_plane.api.app import create_app; print(create_app().handle('GET', '/healthz'))"
```

Serve the minimal HTTP app:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane python3 -m control_plane.cli.main serve-api --host 127.0.0.1 --port 8080
```

The current app is intentionally dependency-light and keeps the handler surface testable in-process.
In this Codex sandbox, live socket bind is blocked, so the primary verification path is direct handler and service tests.

## Current capabilities

- Queue import into DB-backed `task_requests`, `work_items`, and `queue_reconciliations`
- Worker lease acquisition, heartbeat refresh, and stale lease expiry
- Run lifecycle tracking: start, append events, complete, and artifact recording
- Queue export back to validator-compatible `queued` and `evaluated` JSON
- GitHub branch / PR reconciliation into `github_links` and work-item state

## End-to-End Shadow Workflow

Set the DB location for the API routes:
```sh
export RTLCP_DATABASE_URL=sqlite+pysqlite:////tmp/rtlgen-control-plane.db
```

1. Import an existing queue item from the repo into the control-plane DB:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main import-queue \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --queue-path runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json
```

2. Start the minimal API:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main serve-api --host 127.0.0.1 --port 8080
```

3. Acquire the next eligible lease for a worker:
```sh
curl -sS -X POST http://127.0.0.1:8080/api/v1/leases/acquire-next \
  -H 'Content-Type: application/json' \
  -d '{
    "machine_key": "eval-desktop-01",
    "hostname": "eval-desktop-01.local",
    "executor_kind": "docker",
    "capabilities": {"platform": "nangate45", "flow": "openroad"},
    "capability_filter": {"platform": "nangate45", "flow": "openroad"},
    "lease_seconds": 1800
  }'
```

4. Start a run for that lease:
```json
{
  "run_key": "run-softmax-tail-001",
  "attempt": 1,
  "executor_type": "docker",
  "container_image": "rtlgen-dev:latest",
  "checkout_commit": "HEAD",
  "branch_name": "eval/l2_e2e_softmax_macro_tail_v1/s20260308t000000z"
}
```

```text
POST /api/v1/leases/{lease_token}/start-run
```

5. Append run events during execution:
```text
POST /api/v1/runs/{run_key}/events
```

Example body:
```json
{
  "event_type": "command_finished",
  "event_payload": {
    "exit_code": 0,
    "stdout_log": "runs/logs/run-softmax-tail-001.log"
  }
}
```

6. Complete the run with queue-exportable result payload:
```text
POST /api/v1/runs/{run_key}/complete
```

Example body:
```json
{
  "status": "succeeded",
  "result_summary": {
    "rows": 20
  },
  "result_payload": {
    "queue_result": {
      "status": "ok",
      "metrics_rows": [
        "runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/metrics.csv:2"
      ],
      "notes": [
        "shadow control-plane export"
      ]
    }
  },
  "artifacts": [
    {
      "artifact_type": "report",
      "path": "runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/report.md"
    }
  ]
}
```

7. Export the DB-backed item back into queue-compatible JSON:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main export-queue \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_e2e_softmax_macro_tail_v1 \
  --target-state evaluated \
  --target-path /tmp/l2_e2e_softmax_macro_tail_v1.evaluated.json
```

8. Reconcile a branch / PR produced from that exported result:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main reconcile-github \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo yhmtmt/RTLGen \
  --item-id l2_e2e_softmax_macro_tail_v1 \
  --branch-name eval/l2_e2e_softmax_macro_tail_v1/s20260308t000000z \
  --pr-number 99 \
  --pr-url https://github.com/yhmtmt/RTLGen/pull/99 \
  --state pr_open
```

## Verification Notes

- SQLite-backed service tests are the current primary verification path.
- PostgreSQL remains the intended production backing store.
- The initial migration file exists, but `alembic upgrade head` still needs to be verified in a dedicated control-plane Python environment rather than the shared AutoTuner environment.
