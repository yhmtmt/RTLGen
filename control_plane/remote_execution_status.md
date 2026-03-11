# Remote Execution Status

Date: 2026-03-11

Status: proven

## Scope Proven

The cross-host control-plane path is now proven with the notebook and evaluator PC in distinct roles:

- notebook devcontainer role: `server`
- evaluator PC devcontainer role: `evaluator`
- shared PostgreSQL hosted by the notebook devcontainer
- evaluator PC executes real worker runs against the shared DB

## Proven Items

### 1. Cross-Host Remote Worker Execution

Issue:
- `#18` `control_plane: prove remote evaluator worker against shared PostgreSQL`

Result:
- closed as complete
- evaluator PC acquired the lease and executed the real OpenROAD flow
- notebook-side finalize succeeded
- final state reached `AWAITING_REVIEW`

Successful item:
- `l1_remote_softmax_r4_shift5_20260311093105`

Successful run:
- `l1_remote_softmax_r4_shift5_20260311093105_run_65d76a36857b0064`

Final state:
- `runs.status = SUCCEEDED`
- `work_items.state = AWAITING_REVIEW`

### 2. Cross-Host Retry Policy

Issue:
- `#19` `control_plane: evaluator handoff for remote retry probe`

Result:
- closed as complete
- first timed-out run requeued
- second timed-out run stopped retrying and ended terminal `FAILED`

Successful probe item:
- `retry_remote_probe_20260311105728`

Runs:
- pass 1: `retry_remote_probe_20260311105728_run_6753a8f37b641481`
- pass 2: `retry_remote_probe_20260311105728_run_ad6d732a3650cd02`

Final state:
- exactly two runs
- both classified as `command_timeout`
- pass 1: `retry_decision.requeue = true`
- pass 2: `retry_decision.requeue = false`
- `work_items.state = FAILED`

## Operational Meaning

The following are now established:

- cross-host worker leasing works
- cross-host real physical execution works
- notebook/evaluator role split works with one shared image
- bounded retry behavior works across the shared PostgreSQL DB
- remote execution failures can be distinguished from deterministic result failures

## Current Baseline

Primary operating documents:
- [phase2_baseline.md](/workspaces/RTLGen/control_plane/phase2_baseline.md)
- [remote_operator_workflow.md](/workspaces/RTLGen/control_plane/remote_operator_workflow.md)

Proof documents:
- [remote_worker_l1_proof.md](/workspaces/RTLGen/control_plane/remote_worker_l1_proof.md)
- [remote_worker_retry_probe.md](/workspaces/RTLGen/control_plane/remote_worker_retry_probe.md)

## Remaining Work

Remaining work is operational hardening, not feasibility:

- long-running worker supervision
- automatic notebook-side consume/submit orchestration
- richer failure taxonomy and retry policy tuning
- reviewer and merge automation
