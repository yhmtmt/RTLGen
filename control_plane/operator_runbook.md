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
- archival proof/log documents are listed in [archive/README.md](/workspaces/RTLGen/control_plane/archive/README.md)

## Roles

Notebook:
- `RTLCP_ROLE=server`
- usually hosts PostgreSQL when `RTLCP_DB_MODE=local`
- runs the completion loop
- can auto-submit PRs

Evaluator:
- `RTLCP_ROLE=evaluator`
- usually uses the shared remote PostgreSQL when `RTLCP_DB_MODE=remote`
- runs the worker daemon
- executes each item in a disposable clean git worktree at the task `source_commit`
- checks the next assigned item's required source commit before leasing it; the evaluator service repo auto-fetches, updates to a commit containing that source, and re-execs the worker daemon when `RTLCP_AUTO_UPDATE_SOURCE=1`

## Required Host Environment

Notebook host before opening the devcontainer:
```sh
export RTLCP_ROLE=server
export RTLCP_DB_MODE=local
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
export RTLCP_PG_ALLOWED_CIDR='<your evaluator subnet>/24'
export RTLCP_AUTOSTART_COMPLETIONS=1
export RTLCP_SUBMIT=1
export RTLCP_REPO_SLUG='yhmtmt/RTLGen'
```

Evaluator host before opening the devcontainer:
```sh
export RTLCP_ROLE=evaluator
export RTLCP_DB_MODE=remote
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

## Source Revision Contract

Generated work items store the required runtime revision in two places:
- `work_items.source_commit` / `task_requests.source_commit`
- `task_request.request_payload.source_requirement.required_sha`

The worker daemon uses that value before dispatch:
- if the evaluator service repo already contains the required commit, the item runs normally
- if the required commit is reachable from `origin/master`, the service repo is updated and the daemon re-execs itself before leasing the item
- if the commit is missing or the service repo has tracked local modifications, the daemon reports a `source_blocked` or `source_reconcile_error` result instead of running with stale control-plane code

The default evaluator service wrapper enables this behavior:
```sh
RTLCP_AUTO_UPDATE_SOURCE=1
RTLCP_SOURCE_UPDATE_REF=origin/master
RTLCP_RESTART_ON_SOURCE_UPDATE=1
```

Set `RTLCP_AUTO_UPDATE_SOURCE=0` only when deliberately testing stale-checkout behavior.

## Dispatch Behavior

Newly generated work items are created in `DISPATCH_PENDING`.

Normal operator CLI generation now attempts safe auto-dispatch:
- if exactly one eligible fresh evaluator is visible, the item is assigned immediately
- that moves the item to `READY`, which allows the worker to lease it

If an item remains in `DISPATCH_PENDING`, it was not assigned automatically.
Common reasons:
- no fresh evaluator heartbeat
- machine capability mismatch
- multiple eligible evaluators and no unambiguous choice

Manual dispatch fallback:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/rtlgen-eval-clean/control_plane \
python3 -m control_plane.cli.main scheduler \
  --database-url "$RTLCP_DATABASE_URL" \
  dispatch-ready-items
```

Manual explicit assignment:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/rtlgen-eval-clean/control_plane \
python3 -m control_plane.cli.main scheduler \
  --database-url "$RTLCP_DATABASE_URL" \
  assign-item \
  --item-id <item_id> \
  --machine-key <machine_key>
```

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

Request remote evaluator refresh after a control-plane merge:
```sh
/workspaces/RTLGen/control_plane/scripts/request_evaluator_refresh.sh \
  --reason "merged control-plane change; evaluator should pull master and restart daemons"
```

The command opens or updates a GitHub issue with the target commit, pull/update checklist, daemon restart checklist, and a machine-readable evaluator acknowledgement block. Use it instead of drafting ad hoc evaluator update issues.

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
- [resolver_daemons.md](/workspaces/RTLGen/docs/operations/resolver_daemons.md)

Archival proof/status notes:
- [archive/README.md](/workspaces/RTLGen/control_plane/archive/README.md)
