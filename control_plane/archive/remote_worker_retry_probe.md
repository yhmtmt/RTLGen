# Remote Worker Retry Probe

Archive note:
- historical retry proof procedure
- retained for audit and regression context, not routine operation

Date: 2026-03-11

## Purpose

This probe validates bounded retry behavior across two distinct PCs using the shared PostgreSQL control plane:

1. notebook creates a tiny DB-backed work item with one intentionally slow command
2. evaluator PC runs `run-worker` with a short command timeout
3. first worker pass times out and requeues the item
4. second worker pass times out again and ends in terminal `FAILED`

This proves retry policy behavior on the real cross-host workflow, not just in local tests.

## Shared Variables

Notebook:
```sh
export NOTEBOOK_DB_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
export ITEM_ID="retry_remote_probe_$(date -u +%Y%m%d%H%M%S)"
```

Evaluator PC:
```sh
export NOTEBOOK_DB_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
export ITEM_ID='<same item id>'
```

## 1. Notebook Prepare

```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_retry_probe_notebook_prepare.sh
```

## 2. Evaluator Pass 1

```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_retry_probe_evaluator_run.sh
```

Expected after pass 1:
- run status: `FAILED`
- work item state: `READY`
- retry decision: `requeue = true`

## 3. Evaluator Pass 2

Run the same script again:
```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_retry_probe_evaluator_run.sh
```

Expected after pass 2:
- run status: `FAILED`
- work item state: `FAILED`
- retry decision: `requeue = false`

## 4. Notebook Verify

```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_retry_probe_notebook_verify.sh
```

Expected success condition:
- two runs exist for the item
- both runs classify as `command_timeout`
- first run requeues
- second run does not requeue
- final work item state is `FAILED`
