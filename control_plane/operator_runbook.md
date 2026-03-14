# Operator Runbook

This is the canonical control-plane operator document.

Use it for:
- notebook startup
- evaluator startup
- routine daily checks
- restart/recovery actions
- the standard automatic evaluation flow

Historical proof documents remain in this directory, but they are archival.

If you are browsing `control_plane/` directly:
- operator manuals are listed in [README.md](/workspaces/RTLGen/control_plane/README.md)
- archival proof/log documents are listed in [archive_index.md](/workspaces/RTLGen/control_plane/archive_index.md)

## Roles

Notebook:
- `RTLCP_ROLE=server`
- hosts PostgreSQL
- runs the completion loop
- can auto-submit PRs

Evaluator:
- `RTLCP_ROLE=evaluator`
- runs the worker daemon
- executes each item in a disposable clean git worktree at the task `source_commit`

## Required Host Environment

Notebook host before opening the devcontainer:
```sh
export RTLCP_ROLE=server
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
export RTLCP_PG_ALLOWED_CIDR='<your evaluator subnet>/24'
export RTLCP_AUTOSTART_COMPLETIONS=1
export RTLCP_SUBMIT=1
export RTLCP_REPO_SLUG='yhmtmt/RTLGen'
```

Evaluator host before opening the devcontainer:
```sh
export RTLCP_ROLE=evaluator
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
export RTLCP_AUTOSTART_WORKER_DAEMON=1
```

After changing these values:
- recreate or reopen the devcontainer

## Standard Automatic Flow

1. Notebook creates Layer 1 or Layer 2 work items.
2. Evaluator autodaemon leases and executes work automatically.
3. Notebook completion loop consumes `ARTIFACT_SYNC` items automatically.
4. If `RTLCP_SUBMIT=1`, the notebook opens the submission PR automatically.
5. Review and merge the PR normally.

## Routine Commands

Notebook daily check:
```sh
/workspaces/RTLGen/control_plane/scripts/daily_ops.sh
```

Notebook completion restart:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_completion_loop.sh
```

Evaluator worker restart:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_worker_daemon.sh
```

Operator dashboard:
```sh
/workspaces/RTLGen/control_plane/scripts/operator_status.sh --format table
```

Cleanup dry-run:
```sh
/workspaces/RTLGen/control_plane/scripts/cleanup.sh
```

## What Healthy Looks Like

Healthy idle state:
- notebook completion loop running if enabled
- no stale leases
- no growing failed-run set
- no unexpected `ACTIVE_RUNS`
- evaluator worker visible indirectly through shared DB activity

Healthy busy state:
- `READY` items move to `RUNNING`
- `RUNNING` items move to `ARTIFACT_SYNC`
- `ARTIFACT_SYNC` items drain to `AWAITING_REVIEW`
- eligible items open draft PRs automatically when submit is enabled

## Recovery

Restart evaluator worker after pulling latest `master`:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_worker_daemon.sh
```

Restart notebook completion loop after pulling latest `master`:
```sh
/workspaces/RTLGen/control_plane/scripts/restart_completion_loop.sh
```

Expire stale leases:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main scheduler \
  --database-url "$RTLCP_DATABASE_URL" \
  expire-stale-leases
```

Submit an already consumed item manually:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operate-submission \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --item-id <item_id>
```

## Supporting Documents

Primary supporting references:
- [README.md](/workspaces/RTLGen/control_plane/README.md)
- [daily_operations.md](/workspaces/RTLGen/control_plane/daily_operations.md)
- [remote_operator_workflow.md](/workspaces/RTLGen/control_plane/remote_operator_workflow.md)
- [systemd_operator_workflow.md](/workspaces/RTLGen/control_plane/systemd_operator_workflow.md)

Archival proof/status notes:
- `remote_worker_l1_proof.md`
- `remote_worker_retry_probe.md`
- `remote_execution_status.md`
