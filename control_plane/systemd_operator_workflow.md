# Systemd Operator Workflow

Date: 2026-03-12

This is a packaging/reference document, not the primary operator manual.

## Purpose

This is the operational packaging of the already-proven cross-host control-plane flow:

- notebook hosts PostgreSQL and runs completion/submission
- evaluator PC runs the worker daemon
- both machines use the same repo checkout and Python virtualenv
- `systemd` owns restart behavior instead of shell sessions

This does not replace the existing CLI commands. It wraps them.

Important constraint:
- these units require a real `systemd` host or VM
- a normal devcontainer shell where PID 1 is not `systemd` cannot exercise `systemctl` or `journalctl`
- in that environment, validate the wrapper scripts directly and install the units on the host OS instead

## Installed Units

Evaluator PC:
- `rtlgen-evaluator-worker.service`

Notebook:
- `rtlgen-notebook-completions.service`
- `rtlgen-notebook-completions.timer`

Tracked unit files live in:
- [control_plane/systemd](/workspaces/RTLGen/control_plane/systemd)

Tracked wrapper scripts live in:
- [run_worker_daemon_service.sh](/workspaces/RTLGen/control_plane/scripts/run_worker_daemon_service.sh)
- [process_completions_service.sh](/workspaces/RTLGen/control_plane/scripts/process_completions_service.sh)

## Install

Copy the example env files and units.

Evaluator PC:
```sh
sudo mkdir -p /etc/rtlgen /etc/systemd/system
sudo cp /workspaces/RTLGen/control_plane/systemd/evaluator-worker.env.example /etc/rtlgen/evaluator-worker.env
sudo cp /workspaces/RTLGen/control_plane/systemd/rtlgen-evaluator-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rtlgen-evaluator-worker.service
```

Notebook:
```sh
sudo mkdir -p /etc/rtlgen /etc/systemd/system
sudo cp /workspaces/RTLGen/control_plane/systemd/notebook-completions.env.example /etc/rtlgen/notebook-completions.env
sudo cp /workspaces/RTLGen/control_plane/systemd/rtlgen-notebook-completions.service /etc/systemd/system/
sudo cp /workspaces/RTLGen/control_plane/systemd/rtlgen-notebook-completions.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rtlgen-notebook-completions.timer
```

Then edit:
- `/etc/rtlgen/evaluator-worker.env`
- `/etc/rtlgen/notebook-completions.env`

## Required Environment

Evaluator:
- `RTLCP_DATABASE_URL`
- `RTLCP_MACHINE_KEY`
- `RTLCP_HOSTNAME`

Notebook:
- `RTLCP_DATABASE_URL`
- `RTLCP_REPO_SLUG`

Default assumptions:
- service repo root: `/workspaces/rtlgen-eval-clean`
- venv: `/workspaces/RTLGen/control_plane/.venv`

The venv may have an editable install that points at `/workspaces/RTLGen`.
Service launchers must therefore set `PYTHONPATH` to the service repo checkout
they are meant to run:

```sh
PYTHONPATH=/workspaces/rtlgen-eval-clean/control_plane
```

For the local evaluator container, prefer the checked-in wrapper:

```sh
/workspaces/rtlgen-eval-clean/control_plane/scripts/restart_local_control_plane_daemons.sh restart
```

The wrapper starts the API, dev resolver, worker daemon, and eval resolver from
the same service checkout and fails fast if `control_plane` imports resolve
outside that checkout.

## Service Behavior

### Evaluator Worker

`rtlgen-evaluator-worker.service` runs:
- `control_plane/scripts/run_worker_daemon_service.sh`

That wrapper:
- activates the control-plane venv
- runs `run-worker-daemon`
- enforces checkout freshness by default
- uses bounded retry behavior already implemented in the worker

### Notebook Completion

`rtlgen-notebook-completions.service` runs:
- `control_plane/scripts/process_completions_service.sh`

The example env defaults to:
- `RTLCP_SUBMIT=1`

So the timer performs:
1. consume completed `artifact_sync` items
2. publish review package
3. submit eligible real-ingestion items

If you want notebook-side consume-only mode, set:
```sh
RTLCP_SUBMIT=0
```

## Health Checks

Evaluator:
```sh
sudo systemctl status rtlgen-evaluator-worker.service
journalctl -u rtlgen-evaluator-worker.service -n 200 --no-pager
```

Notebook:
```sh
sudo systemctl status rtlgen-notebook-completions.timer
sudo systemctl status rtlgen-notebook-completions.service
journalctl -u rtlgen-notebook-completions.service -n 200 --no-pager
```

Control-plane status:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
export RTLCP_DATABASE_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main submission-status \
  --database-url "$RTLCP_DATABASE_URL" \
  --format table
```

## Recovery

Stale leases:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main scheduler \
  --database-url "$RTLCP_DATABASE_URL" \
  expire-stale-leases
```

Restart evaluator worker:
```sh
sudo systemctl restart rtlgen-evaluator-worker.service
```

Run notebook completion once immediately:
```sh
sudo systemctl start rtlgen-notebook-completions.service
```

## Scope

This packaging assumes:
- current repo checkout on both machines
- shared PostgreSQL already reachable
- no dashboard
- no service-manager secrets integration yet

It is the first operational form, not the final deployment model.
