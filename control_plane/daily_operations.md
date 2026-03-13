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
- devcontainer worker service status
- devcontainer completion service status
- control-plane operator summary
- cleanup dry-run candidates

## Interpretation

Healthy idle state usually looks like:
- worker service: running on evaluator only
- completions service: running on notebook if enabled
- operator status: no stale leases, no growing failed-run set
- cleanup dry-run: only bounded runtime/log noise

Investigate immediately when you see:
- stale active leases
- repeated `checkout_error` or `validation_error`
- `artifact_sync` items not draining
- repeated submission failures

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
