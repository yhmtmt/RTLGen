# Remote Operator Workflow

Date: 2026-03-11

For the current canonical operator path, start with:
- [operator_runbook.md](/workspaces/RTLGen/control_plane/operator_runbook.md)

This is a reference workflow document, not the primary operator manual.

## Purpose

This is the standard cross-host operating mode for the RTLGen control plane:

1. notebook devcontainer runs in `server` role
2. evaluator PC devcontainer runs in `evaluator` role
3. both machines use the same image and control-plane CLI
4. PostgreSQL is hosted by the notebook devcontainer

This document is the operational follow-up to:
- [phase2_baseline.md](/workspaces/RTLGen/control_plane/archive/phase2_baseline.md)
- [phase2_real_ingestion_status.md](/workspaces/RTLGen/control_plane/archive/phase2_real_ingestion_status.md)
- [remote_worker_l1_proof.md](/workspaces/RTLGen/control_plane/archive/remote_worker_l1_proof.md)

## Role Split

Notebook:
- `RTLCP_ROLE=server`
- typically hosts PostgreSQL via `RTLCP_DB_MODE=local`
- defaults `RTLCP_DATABASE_URL` locally if unset
- generates DB-native work items
- consumes completed results
- runs `operate-submission`
- for automatic submission from the completion loop:
  - set `RTLCP_SUBMIT=1`
  - set `RTLCP_REPO_SLUG=yhmtmt/RTLGen`, or let the wrapper derive it from `origin`

Evaluator PC:
- `RTLCP_ROLE=evaluator`
- should use `RTLCP_DB_MODE=remote`
- does not start local PostgreSQL in remote DB mode
- must receive `RTLCP_DATABASE_URL` from host/local environment
- connects to the notebook PostgreSQL over the network
- runs `run-worker`
- executes each task in a disposable clean git worktree at the task `source_commit`

Recommended host-side exports before opening the devcontainer:

Notebook host:
```sh
export RTLCP_ROLE=server
export RTLCP_DB_MODE=local
export RTLCP_AUTOSTART_COMPLETIONS=1
export RTLCP_SUBMIT=1
export RTLCP_REPO_SLUG=yhmtmt/RTLGen
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
```

Evaluator host:
```sh
export RTLCP_ROLE=evaluator
export RTLCP_DB_MODE=remote
export RTLCP_AUTOSTART_WORKER_DAEMON=1
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
```

After changing these values, recreate or reopen the devcontainer so `containerEnv` is refreshed.

## Database URLs

Notebook inside its own devcontainer:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
```

Evaluator PC:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
```

## Standard Flow

### 1. Notebook creates work

Layer 1:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l1-sweep \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  ...
```

Layer 2:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l2-campaign \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  ...
```

### 2. Evaluator PC executes work

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main run-worker \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --machine-key "<unique evaluator machine key>" \
  --hostname "<evaluator hostname>" \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}' \
  --max-items 1
```

Workers enforce checkout freshness by default. The evaluator checkout must be at the task `source_commit` or ahead of it. Use `--allow-stale-checkout` only for manual recovery cases.

### 3. Notebook consumes the completed result

Layer 1:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main consume-l1-result \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --item-id <item_id>
```

Layer 2:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main consume-l2-result \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --item-id <item_id>
```

### 4. Notebook checks submission eligibility

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main submission-status \
  --database-url "$RTLCP_DATABASE_URL" \
  --item-id <item_id> \
  --format table
```

### 5. Notebook opens the submission PR

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operate-submission \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --item-id <item_id>
```

## Standard Output Policy

Use these defaults:
- canonical tracked evidence goes under `runs/`
- remote proof and temporary DB-native sweep outputs can go under:
  - `control_plane/shadow_exports/`

Remote artifact transport is narrower than local output creation:
- workers only inline lightweight canonical evidence under `runs/`
- current transport allowlist is limited to:
  - `runs/index.csv`
  - `runs/designs/**/metrics.csv`
  - `runs/designs/**/macro_manifest.json`
  - `runs/campaigns/**/campaign.json`
  - `runs/campaigns/**/report.md`
  - `runs/campaigns/**/results.csv`
  - `runs/campaigns/**/summary.csv`
  - `runs/campaigns/**/pareto.csv`
  - `runs/campaigns/**/best_point.json`
  - `runs/campaigns/**/objective_sweep.csv`
  - `runs/campaigns/**/objective_sweep.md`
- workers do not transport:
  - `runs/**/work/`
  - `runs/**/artifacts/`
  - `runs/**/comparisons/`
  - `runs/model_cache/**`
  - `control_plane/shadow_exports/**`

Notebook-side completion only materializes that same allowlisted set.

For fresh remote reruns:
- do not reuse an old `out_root` when `--skip_existing` would short-circuit the real physical work
- choose a unique output root per proof or per intentionally fresh rerun

## Success Criteria

The standard remote workflow is healthy when:
- evaluator machine acquires an active lease
- `runs.status = SUCCEEDED`
- `work_items.state = AWAITING_REVIEW`
- notebook-side consumer succeeds
- `submission-status` reports `eligible = True`
- optional `operate-submission` opens or refreshes the draft PR

## Operational Notes

- DB-native generated tasks use:
  - `python3 scripts/validate_runs.py --skip_eval_queue`
- this is intentional
- it prevents unrelated stale queue files elsewhere in the repo from breaking remote/shadow DB-native runs
- full repo-wide queue validation still exists when `--skip_eval_queue` is not used

## Current Proven State

Current proven state:
- local real ingestion for Layer 1 and Layer 2
- cross-host remote evaluator execution against shared PostgreSQL
- evaluator autodaemon pickup
- notebook completion loop consumption
- notebook auto-submit
- clean disposable worker worktrees

This document remains the cross-host reference flow.
For routine operation, prefer the runbook and daily-ops documents.

## Service-Managed Mode

The same workflow can now run under `systemd`:
- evaluator:
  - `rtlgen-evaluator-worker.service`
- notebook:
  - `rtlgen-notebook-completions.service`
  - `rtlgen-notebook-completions.timer`

See:
- [systemd_operator_workflow.md](/workspaces/RTLGen/control_plane/systemd_operator_workflow.md)

In the current devcontainer-based operation, the primary automation path is:
- role-gated devcontainer startup via `.devcontainer/start_control_plane_services.sh`
- background wrappers managed by `.devcontainer/control_plane_service_ctl.sh`

This is preferred over container-internal `systemd` because the evaluator and notebook both run inside devcontainers where PID 1 is not necessarily `systemd`.

Operational restart shortcuts:
- notebook completion loop:
  - `control_plane/scripts/restart_completion_loop.sh`
- evaluator worker daemon:
  - `control_plane/scripts/restart_worker_daemon.sh`
