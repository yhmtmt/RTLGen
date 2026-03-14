# Daily Operations

Use this as the default notebook-side operational check.

## Prerequisites

Notebook shell:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
```

## Default Check

Run:
```sh
/workspaces/RTLGen/control_plane/scripts/daily_ops.sh
```

This reports:
- local devcontainer worker service status
- local devcontainer completion service status
- control-plane operator summary
- cleanup dry-run candidates

## Interpretation

Healthy idle state usually looks like:
- local worker service: not running on notebook
- completions service: running on notebook if enabled
- operator status: no stale leases, no growing failed-run set, no unexpected active runs
- cleanup dry-run: only bounded runtime/log noise

Investigate immediately when you see:
- stale active leases
- repeated `checkout_error` or `validation_error`
- `artifact_sync` items not draining
- repeated submission failures
- active runs with stale heartbeats

## Local vs Remote

On the notebook, `daily_ops.sh` reports local service processes and shared DB state.

That means:
- `local worker service: not running` is normal on the notebook
- remote evaluator activity is shown under `operator-status`, especially:
  - `Active Runs`
  - `Stale Leases`
  - `Recent Failures`

## Follow-up Commands

Inspect operator summary directly:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operator-status \
  --database-url "$RTLCP_DATABASE_URL" \
  --format table
```

Inspect cleanup candidates only:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main cleanup \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen
```

Apply cleanup when the dry run looks safe:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main cleanup \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --apply
```

## Restart Shortcuts

Notebook completion loop:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_completion_loop.sh
```

Evaluator worker daemon:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_worker_daemon.sh
```
