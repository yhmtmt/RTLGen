# RTLGen Control Plane

This subtree hosts the host-side control-plane implementation for RTLGen.

Phase 1 scope:
- import current Git queue items into a DB-backed operational state model,
- lease internal work to deterministic workers,
- export queue-compatible snapshots,
- preserve Git and PRs as the evidence boundary.

Current status:
- `cp-001` through `cp-010` are implemented in the initial shadow-control slice
- in-process API routing, queue import/export, leases, runs, GitHub reconciliation, and the first internal worker loop exist
- artifact-sync and queue round-trip into repo-tracked evaluated snapshots exist
- `cp-010` shadow-run evidence is recorded in `control_plane/shadow_run_cp010.md`
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

## Dedicated Env

Use a dedicated virtualenv for real Phase 1 bring-up instead of the shared AutoTuner Python environment:

```sh
control_plane/scripts/bootstrap_venv.sh
source control_plane/.venv/bin/activate
control_plane/scripts/migrate_smoke.sh
```

What this gives you:
- isolated `alembic`, `sqlalchemy`, and test dependencies
- a clean migration smoke against a fresh local SQLite DB
- an explicit starting point for later PostgreSQL bring-up

## PostgreSQL Bring-up

For real Phase 1 operation, point the control plane at a PostgreSQL server.

Required environment:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@<host>:5432/rtlgen_control_plane'
```

Optional admin URL for auto-creating the target database:
```sh
export RTLCP_PG_ADMIN_URL='postgresql+psycopg://postgres:<admin_password>@<host>:5432/postgres'
```

Bring-up sequence:
```sh
control_plane/scripts/bootstrap_venv.sh
source control_plane/.venv/bin/activate
control_plane/scripts/migrate_postgres.sh
```

What this does:
- optionally creates the target database when `RTLCP_PG_ADMIN_URL` is set
- runs `alembic upgrade head` against PostgreSQL
- verifies that the migrated PostgreSQL database contains the expected control-plane tables

Notes:
- this repo does not assume a local PostgreSQL daemon, Docker, or Podman
- the scripts are designed to work against an already provisioned PostgreSQL service
- `migrate_smoke.sh` remains the fast local SQLite check; `migrate_postgres.sh` is the real bring-up gate

For this repo's devcontainer specifically:
- `.devcontainer/Dockerfile` now installs PostgreSQL
- `.devcontainer/start_control_plane_services.sh` gates local services by `RTLCP_ROLE`
- `.devcontainer/start_postgres.sh` starts the local service and provisions the default `rtlgen` role/database when `RTLCP_ROLE=server`
- `.devcontainer/devcontainer.json` publishes container port `5432` to the notebook host
- `.devcontainer/devcontainer.json` exports a local default:
  - `postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane`
- `.devcontainer/devcontainer.json` forwards optional host-side role selection:
  - `RTLCP_ROLE=server`
  - `RTLCP_ROLE=evaluator`
- `.devcontainer/start_postgres.sh` also configures PostgreSQL for remote password auth:
  - `listen_addresses = '*'`
  - `host ${RTLCP_DB_NAME:-rtlgen_control_plane} ${RTLCP_DB_ROLE:-rtlgen} ${RTLCP_PG_ALLOWED_CIDR:-172.16.0.0/12} scram-sha-256`

That local default is only a convenience for the current phase.
The control-plane scripts still stay generic and continue to honor explicit `RTLCP_DATABASE_URL` overrides.

For a distinct evaluator PC on the same network:
- on the notebook host, use the default role or set `RTLCP_ROLE=server` before rebuild
- on the evaluator PC, set `RTLCP_ROLE=evaluator` before rebuild so the same image boots without a local PostgreSQL daemon
- rebuild/reopen the devcontainer so the `-p 5432:5432` mapping takes effect on the notebook host
- set `RTLCP_PG_ALLOWED_CIDR` before rebuild if you want a narrower evaluator subnet
- use the notebook host IP, not `localhost`, from the evaluator PC:
  - `postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane`

Example host-side setup before opening the container:
```sh
# notebook / server role
export RTLCP_ROLE=server

# evaluator PC
export RTLCP_ROLE=evaluator
```

## Current capabilities

- Queue import into DB-backed `task_requests`, `work_items`, and `queue_reconciliations`
- Direct Layer 1 sweep generation into DB-backed `task_requests` and `work_items`
- Worker lease acquisition, heartbeat refresh, and stale lease expiry
- Run lifecycle tracking: start, append events, complete, and artifact recording
- Internal worker loop execution from queue `command_manifest` with per-command logs and staged outputs
- Failure classification and bounded retry for internal worker runs
- Artifact sync from `artifact_sync` work items into repo-tracked evaluated queue snapshots
- Queue export back to validator-compatible `queued` and `evaluated` JSON
- GitHub branch / PR reconciliation into `github_links` and work-item state

## Operational Commands

Long-running evaluator loop:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main run-worker-daemon \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --machine-key "<machine_key>" \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}'
```

By default, workers reject stale evaluator checkouts. A work item's `source_commit` is treated as the minimum required commit, so `HEAD` may match it exactly or be ahead of it. Use `--allow-stale-checkout` only as a temporary operator override.

Notebook-side completion processing:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main process-completions \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen
```

Remote completion materializes only the lightweight canonical evidence allowlist under `runs/`.
It does not rematerialize:
- `runs/**/work/`
- `runs/**/artifacts/`
- `runs/**/comparisons/`
- `runs/model_cache/**`
- `control_plane/shadow_exports/**`

Notebook-side completion processing plus submission:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main process-completions \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --submit
```

## Systemd Packaging

The proven cross-host flow is now packaged for `systemd`:
- evaluator daemon service
- notebook completion service
- notebook completion timer

Tracked files:
- [control_plane/systemd](/workspaces/RTLGen/control_plane/systemd)
- [systemd_operator_workflow.md](/workspaces/RTLGen/control_plane/systemd_operator_workflow.md)

Wrapper scripts:
- [run_worker_daemon_service.sh](/workspaces/RTLGen/control_plane/scripts/run_worker_daemon_service.sh)
- [process_completions_service.sh](/workspaces/RTLGen/control_plane/scripts/process_completions_service.sh)

Use the example env files as the starting point:
- `control_plane/systemd/evaluator-worker.env.example`
- `control_plane/systemd/notebook-completions.env.example`

## Devcontainer Autostart

The primary operator mode in the current environment is now devcontainer startup, not container-internal `systemd`.

Role-gated behavior:
- `RTLCP_ROLE=server`
  - starts local PostgreSQL
  - defaults `RTLCP_DATABASE_URL` to local PostgreSQL if unset
  - does not start notebook completion automatically unless `RTLCP_AUTOSTART_COMPLETIONS=1`
- `RTLCP_ROLE=evaluator`
  - skips local PostgreSQL
  - requires `RTLCP_DATABASE_URL` from host/local env
  - starts the worker daemon automatically unless `RTLCP_AUTOSTART_WORKER_DAEMON=0`

Helper scripts:
- [.devcontainer/control_plane_service_ctl.sh](/workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh)
- [.devcontainer/run_completion_loop.sh](/workspaces/RTLGen/.devcontainer/run_completion_loop.sh)

Examples:
```sh
# notebook
export RTLCP_ROLE=server
export RTLCP_AUTOSTART_COMPLETIONS=1
export RTLCP_SUBMIT=1
export RTLCP_REPO_SLUG=yhmtmt/RTLGen
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
```

```sh
# evaluator
export RTLCP_ROLE=evaluator
export RTLCP_AUTOSTART_WORKER_DAEMON=1
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
```

These exports are host-side inputs for devcontainer startup.
After changing them, recreate or reopen the devcontainer so `containerEnv` is refreshed.

Runtime state is written under:
- `/tmp/rtlgen-control-plane/worker.pid`
- `/tmp/rtlgen-control-plane/worker.log`
- `/tmp/rtlgen-control-plane/completions.pid`
- `/tmp/rtlgen-control-plane/completions.log`

When `RTLCP_SUBMIT=1`, the completion wrapper submits automatically if it has a repo slug.
It prefers `RTLCP_REPO_SLUG`, and otherwise derives the slug from the checkout `origin` URL.

Worker execution no longer uses the evaluator's mutable main checkout directly.
Each item is executed in a disposable detached git worktree at the task `source_commit`,
so new tracked configs and other repo inputs come from Git rather than local dirt.

Operator live status:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operator-status \
  --database-url "$RTLCP_DATABASE_URL" \
  --format table
```

The operator dashboard now includes:
- `State Counts`
- `Active Runs`
- `Stale Leases`
- `Recent Failures`
- `Recent Submissions`

For notebook-side daily checks:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
/workspaces/RTLGen/control_plane/scripts/daily_ops.sh
```

That daily check reports:
- local worker/completion service status
- shared DB operator summary
- cleanup dry-run candidates

Cleanup retention can be tuned per class:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main cleanup \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --runtime-max-age-days 3 \
  --log-max-age-days 14 \
  --db-max-age-days 30
```

Daily notebook operations:
```sh
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
/workspaces/RTLGen/control_plane/scripts/daily_ops.sh
```

The daily-ops wrapper reports:
- devcontainer worker/completion service status
- operator dashboard state summary
- cleanup dry-run candidates

Cleanup dry-run:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main cleanup \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen
```

Apply cleanup:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main cleanup \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --apply
```

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
- writes `control_plane/shadow_exports/evaluated/<item_id>.json` by default for shadow-safe validation,
- can still write `runs/eval_queue/openroad/evaluated/<item_id>.json` when `--target-path` is supplied explicitly,
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

## Direct Layer 1 Sweep Generation

The first Layer 1 generator can create an OpenROAD sweep work item directly in the DB without first authoring a queue JSON file.

Example:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l1-sweep \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --sweep-path runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json \
  --configs examples/config_softmax_rowwise_int8.json examples/config_softmax_rowwise_int8_r8_acc20.json \
  --platform nangate45 \
  --out-root runs/designs/activations \
  --requested-by @yhmtmt
```

This generator currently targets a narrow scope:
- Layer 1
- OpenROAD
- config-driven sweeps invoked through `scripts/run_sweep.py`

The matching Layer 1 result consumer reads a completed `l1_sweep` run and emits a reviewable promotion proposal JSON:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main consume-l1-result \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l1_sweep_nangate45_softmax_demo
```

Default output:
- `control_plane/shadow_exports/l1_promotions/<item_id>.json`

Current behavior:
- chooses the best `status=ok` row per generated `metrics.csv`
- ranks by:
  - `critical_path_ns`
  - then `die_area`
  - then `total_power_mw`
- writes a proposal artifact for review; it does not auto-edit candidate manifests

## Direct Layer 2 Campaign Generation

The first Layer 2 generator can create a campaign-backed work item directly in the DB from a tracked `campaign.json`.

Example:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l2-campaign \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --campaign-path runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/campaign.json \
  --objective-profiles-json runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/objective_profiles.json \
  --requested-by @yhmtmt
```

Current scope:
- Layer 2
- OpenROAD
- campaign definitions already tracked in the repo
- generates a `l2_campaign` work item with:
  - `validate_campaign`
  - `run_campaign`
  - `report_campaign`
  - optional `objective_sweep`
  - `validate_runs`

The matching Layer 2 result consumer reads a completed `l2_campaign` run and emits a reviewable decision proposal JSON:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main consume-l2-result \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_campaign_demo
```

Default output:
- `control_plane/shadow_exports/l2_decisions/<item_id>.json`

Current behavior:
- reads tracked campaign outputs such as:
  - `best_point.json`
  - `summary.csv`
  - `objective_sweep.csv`
- emits:
  - recommended `arch_id`
  - recommended `macro_mode`
  - objective-profile winners
- writes a decision proposal for review; it does not auto-edit docs or queue items

## Review Package Publishing

Completed DB-native runs can publish a review-ready package directly from the control-plane DB.

Example:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main publish-review \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_real_softmax_shadow_single \
  --evaluator-id control_plane \
  --executor @control_plane
```

Default outputs:
- `control_plane/shadow_exports/review/<item_id>/evaluated.json`
- `control_plane/shadow_exports/review/<item_id>/review_package.json`

The review package includes:
- a normalized evaluated queue snapshot
- the linked promotion or decision proposal artifact when one exists
- branch, title, body fields, and checklist material for a review PR

## Submission Bridge

The submission bridge turns a published review package into a bot-owned branch in a temporary git worktree.

Example:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main prepare-submission \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --item-id l2_real_softmax_shadow_single \
  --evaluator-id control_plane \
  --executor @control_plane
```

Outputs:
- a temporary git worktree with a local branch matching the review package branch
- forced-added ignored review files committed on that branch
- `control_plane/shadow_exports/review/<item_id>/submission_manifest.json`

The submission manifest includes:
- branch name
- commit SHA
- PR title
- PR body file path
- the exact `gh pr create --draft ...` command to run next

## Submission Execution

The execution bridge can push a prepared submission branch and open the draft PR, then reconcile the returned PR metadata into `github_links`.

Example:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main execute-submission \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --item-id l2_real_softmax_shadow_single
```

This step:
- reuses an existing submission manifest when present
- otherwise prepares the submission branch first
- runs `git push -u origin <branch>`
- runs `gh pr create --draft ...`
- runs `gh pr view ... --json ...`
- reconciles the resulting PR metadata back into the control-plane DB

## One-Shot Operator Command

For normal operator use, the full chain can run in one command:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operate-submission \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --item-id l2_real_softmax_shadow_single
```

List review-ready and blocked items:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main submission-status \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db
```

Only list currently eligible items:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main submission-status \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --eligible-only
```

Tabular terminal view:

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main submission-status \
  --database-url sqlite+pysqlite:////tmp/rtlgen-control-plane.db \
  --format table
```

Stages:
1. publish review package
2. prepare submission branch and worktree
3. push branch, open draft PR, reconcile PR metadata

Recovery behavior:
- review publishing is idempotent
- if the submission manifest already exists, the operator command reuses it instead of trying to recreate the branch
- the final operator checkpoint is written to:
  - `control_plane/shadow_exports/review/<item_id>/operator_submission.json`

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
