# RTLGen Control Plane

This subtree hosts the host-side control-plane implementation for RTLGen.

Phase 1 scope:
- import current Git queue items into a DB-backed operational state model,
- lease internal work to deterministic workers,
- export queue-compatible snapshots,
- preserve Git and PRs as the evidence boundary.

Current status:
- `cp-001` through `cp-009` are implemented in the initial shadow-control slice
- in-process API routing, queue import/export, leases, runs, GitHub reconciliation, and the first internal worker loop exist
- artifact-sync and queue round-trip into repo-tracked evaluated snapshots exist
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
- Internal worker loop execution from queue `command_manifest` with per-command logs and staged outputs
- Artifact sync from `artifact_sync` work items into repo-tracked evaluated queue snapshots
- Queue export back to validator-compatible `queued` and `evaluated` JSON
- GitHub branch / PR reconciliation into `github_links` and work-item state

## End-to-End Shadow Workflow

Set the DB location:
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

2. Execute one internal worker pass:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main run-worker \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --machine-key eval-desktop-01 \
  --hostname eval-desktop-01.local \
  --capabilities-json '{"platform":"nangate45","flow":"openroad"}' \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}' \
  --lease-seconds 1800 \
  --heartbeat-seconds 30 \
  --max-items 1
```

The worker loop acquires a lease, starts a run, heartbeats while commands execute, writes per-command logs, stages expected outputs, and completes the run in one pass.

3. Sync the completed run into the repo-tracked evaluated queue snapshot:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main sync-artifacts \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_e2e_softmax_macro_tail_v1 \
  --evaluator-id control_plane \
  --host eval-desktop-01.local \
  --executor @control_plane
```

This step:
- normalizes `metrics_rows` into validator-compatible reference objects,
- writes `runs/eval_queue/openroad/evaluated/<item_id>.json`,
- attaches a `queue_snapshot` artifact to the run,
- moves the work item to `awaiting_review`.

4. Export the DB-backed item back into queue-compatible JSON manually if needed:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main export-queue \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_e2e_softmax_macro_tail_v1 \
  --target-state evaluated \
  --target-path /tmp/l2_e2e_softmax_macro_tail_v1.evaluated.json
```

5. Reconcile a branch / PR produced from that exported result:
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

## Manual API Flow

The in-process HTTP routes remain available if you want to exercise the lifecycle step-by-step rather than through `run-worker`:

- `POST /api/v1/leases/acquire-next`
- `POST /api/v1/leases/{lease_token}/start-run`
- `POST /api/v1/leases/{lease_token}/heartbeat`
- `POST /api/v1/runs/{run_key}/events`
- `POST /api/v1/runs/{run_key}/complete`
- `POST /api/v1/queue/export/{item_id}`
- `POST /api/v1/github/reconcile`

## Verification Notes

- SQLite-backed service tests are the current primary verification path.
- PostgreSQL remains the intended production backing store.
- The initial migration file exists, but `alembic upgrade head` still needs to be verified in a dedicated control-plane Python environment rather than the shared AutoTuner environment.
