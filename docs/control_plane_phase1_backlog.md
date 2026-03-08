# Control Plane Phase 1 Backlog and Repository Layout

## Purpose
Turn the Phase 1 control-plane specification into an implementation backlog with:
- milestones,
- deliverables,
- repository layout,
- test gates,
- execution order.

Related documents:
- [agent_control_plane_plan.md](./agent_control_plane_plan.md)
- [internal_external_evaluator_policy.md](./internal_external_evaluator_policy.md)
- [control_plane_phase1_spec.md](./control_plane_phase1_spec.md)

## Phase 1 Outcome
At the end of Phase 1, RTLGen should have a working shadow control plane that can:
- import current queue JSON items into a DB,
- lease internal work to workers,
- record runs and artifacts explicitly,
- export queue-compatible snapshots,
- coexist with the current PR-based evaluator workflow.

Phase 1 should not yet try to automate cross-layer scientific decisions.
It should first make execution state explicit and reliable.

## Recommended Repository Layout
Do not spread the control-plane code across unrelated existing directories.
Create a dedicated tree.

### Proposed layout
```text
control_plane/
  README.md
  pyproject.toml
  alembic.ini
  control_plane/
    __init__.py
    config.py
    logging.py
    db.py
    clock.py
    ids.py
    api/
      __init__.py
      app.py
      deps.py
      routes_health.py
      routes_queue.py
      routes_leases.py
      routes_runs.py
      routes_workers.py
    models/
      __init__.py
      task_requests.py
      work_items.py
      worker_machines.py
      worker_leases.py
      runs.py
      run_events.py
      artifacts.py
      github_links.py
      queue_reconciliations.py
    schemas/
      __init__.py
      queue_item.py
      leases.py
      runs.py
      workers.py
      github.py
    services/
      __init__.py
      queue_importer.py
      queue_exporter.py
      scheduler.py
      lease_service.py
      run_service.py
      worker_service.py
      github_bridge.py
      reconciliation_service.py
    cli/
      __init__.py
      main.py
      import_queue.py
      export_queue.py
      run_scheduler.py
      run_worker.py
      reconcile_github.py
    workers/
      __init__.py
      executor.py
      checkout.py
      command_runner.py
      artifact_stage.py
      heartbeat.py
    migrations/
      versions/
    tests/
      test_queue_importer.py
      test_queue_exporter.py
      test_scheduler.py
      test_leases.py
      test_run_service.py
      test_reconciliation.py
```

## Why This Layout
- `api/` isolates the HTTP surface.
- `models/` and `schemas/` separate DB persistence from wire format.
- `services/` keeps scheduling and reconciliation logic out of route handlers.
- `workers/` isolates deterministic execution logic.
- `cli/` allows operations without requiring a full server deployment during bring-up.
- `tests/` keeps the control-plane test surface local to the subsystem.

This is the minimum structure that will not collapse into one unreadable Python script.

## Recommended Technology Choices
For Phase 1, keep the stack conservative.

### Runtime
- Python 3.x

### Server
- FastAPI or a similarly small HTTP layer

### ORM / SQL
- SQLAlchemy 2.x or direct SQL with a thin repository layer

### Migrations
- Alembic

### Testing
- `pytest` for the control-plane subtree
- temporary PostgreSQL instance or transactional test DB

### Packaging
- isolated `pyproject.toml` under `control_plane/`

Reason:
- the repo already uses Python heavily,
- queue import/export and worker orchestration are primarily I/O and state management tasks,
- Phase 1 does not justify a more operationally heavy stack.

## Milestone Plan

### Milestone 0: Skeleton and conventions
Goal:
- create the subsystem skeleton and coding conventions without changing the current evaluator workflow.

Deliverables:
- `control_plane/` directory scaffold
- local package metadata
- migration tooling initialized
- basic app bootstrapping
- health endpoint
- README describing local dev startup

Acceptance:
- module imports cleanly
- empty app starts
- migration tooling can create a baseline revision

Do not add business logic here yet.

### Milestone 1: Database foundation
Goal:
- implement the Phase 1 schema and migration chain.

Deliverables:
- SQLAlchemy models or equivalent for all Phase 1 tables
- initial Alembic migration
- DB session/config wiring
- seed utility for registering worker machines

Acceptance:
- fresh DB can migrate from zero to head
- schema matches [control_plane_phase1_spec.md](./control_plane_phase1_spec.md)
- uniqueness and partial-active-lease constraints are enforced

Key tasks:
1. add base model definitions
2. implement state enums centrally
3. create migration `0001_initial`
4. add DB smoke tests

### Milestone 2: Queue importer
Goal:
- import existing Git queue items into DB without loss.

Deliverables:
- `queue_importer.py`
- `POST /api/v1/queue/import`
- CLI import command
- reconciliation log writes

Acceptance:
- importing a real queued item creates `task_requests`, `work_items`, and `queue_reconciliations`
- repeated import is idempotent
- conflicting payloads are detected and reported

Key tasks:
1. implement queue JSON parsing using current schema assumptions
2. map queue fields into DB entities
3. preserve raw payload in `request_payload`
4. record queue path and content hash
5. add tests using real repo queue fixtures

### Milestone 3: Scheduler and leases
Goal:
- make internal work assignment explicit and safe.

Deliverables:
- `scheduler.py`
- `lease_service.py`
- `POST /api/v1/leases/acquire-next`
- `POST /api/v1/leases/{lease_token}/heartbeat`
- stale lease reaper CLI/job

Acceptance:
- only one active lease exists per work item
- lease expiry returns item to `ready` when appropriate
- heartbeat extends lease correctly
- scheduler respects priority ordering and machine capability filters

Key tasks:
1. implement transactional lease acquisition
2. implement machine capability matching
3. add lease expiration job
4. record lease events
5. add concurrency tests for double-acquire races

### Milestone 4: Run tracking
Goal:
- represent execution attempts explicitly instead of inferring them from PRs.

Deliverables:
- `run_service.py`
- `POST /api/v1/leases/{lease_token}/start-run`
- `POST /api/v1/runs/{run_key}/events`
- `POST /api/v1/runs/{run_key}/complete`

Acceptance:
- a leased work item can produce a run attempt with events and terminal status
- run attempts are append-only by `(work_item_id, attempt)`
- artifact references can be attached to the run

Key tasks:
1. implement run creation from a valid lease
2. implement append-only event logging
3. implement terminal completion semantics
4. attach artifact metadata at completion time
5. add tests for state transitions from `leased -> running -> artifact_sync/awaiting_review/failed`

### Milestone 5: Minimal worker
Goal:
- create one internal worker implementation that can execute existing queue commands.

Deliverables:
- `workers/executor.py`
- `workers/checkout.py`
- `workers/command_runner.py`
- `workers/heartbeat.py`
- `cli/run_worker.py`

Acceptance:
- worker can lease a DB-backed item
- worker can run command manifests in order
- worker can emit heartbeat and run events
- worker can mark success/failure cleanly

Key tasks:
1. local repo checkout/worktree materialization
2. deterministic command execution
3. stdout/stderr capture to transient files
4. heartbeat thread or timer
5. failure classification hooks

Constraint:
- Phase 1 worker should execute commands exactly as authored unless policy explicitly says otherwise.

### Milestone 6: Queue exporter
Goal:
- export DB-backed state back into current queue JSON format.

Deliverables:
- `queue_exporter.py`
- `POST /api/v1/queue/export/{item_id}`
- CLI export command

Acceptance:
- exported `queued` item matches current schema shape
- exported `evaluated` item is validator-compatible when run data is complete
- exported item keeps the same `item_id` and task semantics as the original import

Key tasks:
1. map DB state back to queue schema
2. fill result payload from `runs` and `artifacts`
3. preserve `handoff` shape
4. add export fixture tests
5. add round-trip import/export tests

### Milestone 7: GitHub linkage reconciliation
Goal:
- attach branches and PRs to DB runs and work items.

Deliverables:
- `github_bridge.py`
- `github_links` persistence
- CLI reconciliation command

Acceptance:
- a known PR can be linked to the correct `item_id`
- merge state updates `work_items.state`
- evaluator-issued PRs can be represented in DB even if created outside the control plane

Key tasks:
1. define lookup strategy by branch name and/or queue `item_id`
2. ingest PR metadata
3. handle merged/closed/open states
4. add reconciliation tests with mocked GitHub payloads

### Milestone 8: First end-to-end shadow run
Goal:
- prove that the control plane works on one real internal evaluation item without replacing current repo workflows.

Deliverables:
- one documented dry run using a real queue item
- imported DB state
- leased worker execution
- exported evaluated snapshot
- validation proof

Acceptance:
- `scripts/validate_runs.py` still passes on the exported snapshot
- no queue-schema change was required
- internal execution state is visible in DB
- Git evidence remains reviewable in the existing repo workflow

This is the first milestone where the control plane becomes useful to the project instead of merely existing.

## Backlog by Workstream

### Workstream A: Data model
Tasks:
- define all enums centrally
- implement models
- create migrations
- add fixture builders

Priority:
- highest

Dependency:
- none

### Workstream B: Queue mapping
Tasks:
- implement importer
- implement exporter
- add round-trip tests
- add reconciliation records

Priority:
- highest

Dependency:
- data model

### Workstream C: Scheduling and leases
Tasks:
- scheduler selection logic
- machine capability filters
- lease acquisition transaction
- expiry/reaper

Priority:
- highest

Dependency:
- data model

### Workstream D: Worker execution
Tasks:
- checkout logic
- command execution
- event emission
- heartbeat
- artifact staging metadata

Priority:
- high

Dependency:
- scheduler and runs API

### Workstream E: GitHub linkage
Tasks:
- PR/branch link storage
- reconciliation command
- merge-state updates

Priority:
- medium

Dependency:
- runs and queue export

### Workstream F: Operator tooling
Tasks:
- CLI commands
- health/status endpoints
- documentation for local bring-up

Priority:
- medium

Dependency:
- core services

## Proposed Issue Breakdown
A clean implementation backlog should map roughly to these issues:

1. `cp-001`: scaffold `control_plane/` package and local dev setup
2. `cp-002`: add initial DB schema and migrations
3. `cp-003`: implement queue importer and idempotent reconciliation log
4. `cp-004`: implement scheduler and lease acquisition
5. `cp-005`: implement lease heartbeat and expiry handling
6. `cp-006`: implement run tracking and run events
7. `cp-007`: implement minimal internal worker executor
8. `cp-008`: implement queue exporter for queued/evaluated snapshots
9. `cp-009`: implement GitHub branch/PR reconciliation
10. `cp-010`: perform one real shadow-run validation against an existing queue item

This is a better cut than mixing importer, scheduler, worker, and GitHub logic into one oversized first PR.

## Test Strategy

### Unit tests
Required for:
- import mapping
- export mapping
- lease uniqueness
- lease expiry
- run state transitions
- reconciliation conflict detection
- machine capability filtering

### Integration tests
Required for:
- import -> lease -> run -> export
- round-trip queue compatibility
- PR linkage reconciliation

### Repo fixture policy
Use real queue-item fixtures copied from current `runs/eval_queue/openroad/` examples.
Do not invent a parallel fake schema for tests.

## Operational Bring-Up Sequence
Recommended bring-up order on a dev machine:
1. start PostgreSQL
2. run migrations
3. register one worker machine
4. import one real queued item
5. inspect DB state
6. start scheduler or use direct acquire-next endpoint
7. run worker in dry-run mode first
8. run worker against a small real item
9. export snapshot and compare to original queue semantics

## Risks and Countermeasures

### Risk: queue schema drift
Countermeasure:
- queue importer/exporter tests must use real repo examples
- keep queue mapping code isolated in one service module

### Risk: worker becomes too smart
Countermeasure:
- keep deterministic executor separate from future reasoning agents
- forbid command rewriting in Phase 1 except by explicit policy

### Risk: DB and Git state diverge silently
Countermeasure:
- reconciliation table is mandatory
- importer/exporter should log conflicts instead of silently overwriting

### Risk: trying to automate publication too early
Countermeasure:
- Phase 1 only needs linkage and compatibility
- auto PR creation can wait until after one successful shadow run

## Definition of Done for Phase 1
Phase 1 is done when:
- `control_plane/` exists with the layout above or a close equivalent,
- DB schema is migrated and tested,
- real queue items can be imported and exported losslessly enough for validator compatibility,
- internal workers can lease and run tasks,
- run attempts and artifacts are explicitly recorded,
- PR linkage can be reconciled,
- one real shadow-run has been executed successfully.

## What Should Happen Next After Phase 1
Only after Phase 1 is stable should the project add:
- Layer 1 generator agent,
- Layer 1 consumer agent,
- Layer 2 generator agent,
- Layer 2 consumer agent,
- more automated publication flows.

This order is important.
Without explicit state and leases, agent autonomy will just automate ambiguity.

## Decision Summary
Recommended immediate implementation strategy:
1. create `control_plane/` as an isolated subsystem,
2. build DB schema first,
3. implement queue import/export second,
4. add leases and worker execution third,
5. validate on one real queue item before adding more intelligence.

That is the shortest path from planning to a control plane that the project can actually trust.
