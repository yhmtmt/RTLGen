# Control Plane Phase 1 Implementation Spec

## Purpose
Define the first implementable slice of the RTLGen host-side control plane.

This document turns the planning documents into a concrete Phase 1 scope:
- database schema,
- lease model,
- worker protocol,
- Git queue importer/exporter,
- minimal service boundaries,
- migration constraints.

It is intentionally limited to Phase 1.
It does not define the full autonomous Layer 1 / Layer 2 agent logic yet.

Related documents:
- [agent_control_plane_plan.md](./agent_control_plane_plan.md)
- [internal_external_evaluator_policy.md](./internal_external_evaluator_policy.md)

## Phase 1 Goal
Build a shadow control plane that can:
1. ingest existing queue JSON items into a DB,
2. represent work items and execution attempts explicitly,
3. lease work to internal workers,
4. export queue-compatible JSON snapshots,
5. preserve the current PR/evaluated-item artifact model.

Phase 1 is successful when:
- internal work can be tracked by DB state instead of only Git state,
- queue JSON remains compatible with current evaluator expectations,
- no reproducibility information is lost,
- no existing evaluation artifact format must be rewritten.

## Scope

### In scope
- PostgreSQL schema
- control-plane API for internal use
- scheduler lease semantics
- worker heartbeat/report protocol
- queue JSON import/export
- GitHub linkage fields in DB
- internal-worker execution model
- compatibility with current `runs/eval_queue/openroad/*.json`

### Out of scope
- public multi-tenant contribution portal
- replacing PR review with an internal UI
- autonomous Layer 1 / Layer 2 decision-making
- object-store retention policy beyond minimal transient artifact tracking
- top-level project-wide auth/SSO design

## Core Rules
1. DB is authoritative for internal operational state.
2. Git remains authoritative for committed evidence.
3. Queue JSON remains a compatibility format and audit snapshot.
4. Internal workers get work by lease, not by Git polling.
5. External contributors remain PR-based and out of DB write scope.

## Service Boundary

### Required Phase 1 components
- `cp-api`
- `cp-scheduler`
- `cp-worker`
- `cp-queue-sync`
- `cp-github-bridge`

### Responsibilities

#### `cp-api`
- accept task imports
- list work items and runs
- expose lease and heartbeat endpoints for internal workers
- expose reconciliation state

#### `cp-scheduler`
- choose next runnable work item
- assign worker leases
- expire stale leases
- enforce simple priority ordering

#### `cp-worker`
- request lease
- materialize checkout and execution environment
- run deterministic commands
- report state/heartbeats
- stage outputs for artifact sync

#### `cp-queue-sync`
- import `queued` and `evaluated` JSON items from Git
- export DB work items back into queue-compatible JSON snapshots
- reconcile queue item identity with DB identity

#### `cp-github-bridge`
- link runs to branches and PRs
- optionally create internal publication branches/PRs in later phases
- record PR metadata in DB

## Database Schema

### Naming policy
Use explicit tables with append-friendly run history.
Do not overload one table for both task definition and execution attempt state.

### `task_requests`
Represents a human- or agent-authored request before expansion.

Columns:
- `id` `uuid` primary key
- `request_key` `text` unique not null
- `source` `text` not null
  - examples: `git_queue_import`, `api`, `agent:l1_generator`
- `requested_by` `text` not null
- `title` `text` not null
- `description` `text` not null default `''`
- `layer` `text` not null
  - `layer1`, `layer2`, `meta`
- `flow` `text` not null
  - `openroad`
- `priority` `integer` not null default `1`
- `request_payload` `jsonb` not null
- `source_commit` `text`
- `created_at` `timestamptz` not null default `now()`

Indexes:
- unique index on `request_key`
- index on `(layer, flow, created_at desc)`

### `work_items`
Represents a concrete executable unit.

Columns:
- `id` `uuid` primary key
- `work_item_key` `text` unique not null
- `task_request_id` `uuid` references `task_requests(id)` not null
- `item_id` `text` unique not null
  - matches queue JSON `item_id`
- `layer` `text` not null
- `flow` `text` not null
- `platform` `text` not null
- `task_type` `text` not null
  - examples: `l1_sweep`, `macro_harden`, `l2_campaign`
- `state` `text` not null
  - `draft`, `ready`, `leased`, `running`, `artifact_sync`, `awaiting_review`, `merged`, `failed`, `blocked`, `superseded`
- `priority` `integer` not null
- `source_mode` `text`
  - mirrors queue `task.source_mode`
- `input_manifest` `jsonb` not null
- `command_manifest` `jsonb` not null
- `expected_outputs` `jsonb` not null
- `acceptance_rules` `jsonb` not null
- `queue_snapshot_path` `text`
- `source_commit` `text`
- `created_at` `timestamptz` not null default `now()`
- `updated_at` `timestamptz` not null default `now()`

Constraints:
- `item_id` globally unique
- `state` check against allowed values

Indexes:
- index on `(state, priority desc, created_at asc)`
- index on `(layer, platform, state)`

### `worker_machines`
Represents available internal evaluator machines.

Columns:
- `id` `uuid` primary key
- `machine_key` `text` unique not null
- `hostname` `text` not null
- `executor_kind` `text` not null
  - `docker`, `local_container`, `baremetal`
- `capabilities` `jsonb` not null
  - example fields: `cpu`, `ram_gb`, `openroad_version`, `warm_model_cache`, `tags`
- `active` `boolean` not null default true
- `last_seen_at` `timestamptz`
- `created_at` `timestamptz` not null default `now()`

Indexes:
- unique index on `machine_key`
- gin index on `capabilities`

### `worker_leases`
Represents the current lease for a runnable work item.

Columns:
- `id` `uuid` primary key
- `work_item_id` `uuid` references `work_items(id)` not null
- `machine_id` `uuid` references `worker_machines(id)` not null
- `lease_token` `text` unique not null
- `status` `text` not null
  - `active`, `expired`, `released`, `revoked`
- `leased_at` `timestamptz` not null default `now()`
- `expires_at` `timestamptz` not null
- `last_heartbeat_at` `timestamptz`

Constraints:
- at most one `active` lease per `work_item_id`

Indexes:
- index on `(status, expires_at)`
- index on `(machine_id, status)`

Implementation note:
- use a partial unique index on `work_item_id` where `status='active'`

### `runs`
Represents one execution attempt.

Columns:
- `id` `uuid` primary key
- `run_key` `text` unique not null
- `work_item_id` `uuid` references `work_items(id)` not null
- `lease_id` `uuid` references `worker_leases(id)`
- `attempt` `integer` not null
- `executor_type` `text` not null
  - `internal_worker`, `external_pr`, `agent_assisted_worker`
- `machine_id` `uuid` references `worker_machines(id)`
- `container_image` `text`
- `checkout_commit` `text`
- `branch_name` `text`
- `status` `text` not null
  - `starting`, `running`, `succeeded`, `failed`, `canceled`, `timed_out`
- `started_at` `timestamptz`
- `completed_at` `timestamptz`
- `result_summary` `text` not null default `''`
- `result_payload` `jsonb`
- `created_at` `timestamptz` not null default `now()`

Constraints:
- unique `(work_item_id, attempt)`

Indexes:
- index on `(work_item_id, attempt desc)`
- index on `(status, started_at desc)`

### `run_events`
Append-only execution event log.

Columns:
- `id` `bigserial` primary key
- `run_id` `uuid` references `runs(id)` not null
- `event_time` `timestamptz` not null default `now()`
- `event_type` `text` not null
  - `lease_acquired`, `checkout_ready`, `command_started`, `command_finished`, `heartbeat`, `artifact_staged`, `validation_failed`, `pr_linked`
- `event_payload` `jsonb` not null default `'{}'::jsonb`

Indexes:
- index on `(run_id, event_time asc)`

### `artifacts`
References transient or committed artifacts.

Columns:
- `id` `uuid` primary key
- `run_id` `uuid` references `runs(id)` not null
- `kind` `text` not null
  - `metrics_csv`, `report_md`, `macro_manifest`, `queue_snapshot`, `log_bundle`, `result_json`
- `storage_mode` `text` not null
  - `transient`, `repo`
- `path` `text` not null
- `sha256` `text`
- `metadata` `jsonb` not null default `'{}'::jsonb`
- `created_at` `timestamptz` not null default `now()`

Indexes:
- index on `(run_id, kind)`
- index on `(storage_mode, kind)`

### `github_links`
Tracks branch/PR relationships.

Columns:
- `id` `uuid` primary key
- `work_item_id` `uuid` references `work_items(id)` not null
- `run_id` `uuid` references `runs(id)`
- `repo` `text` not null
- `branch_name` `text`
- `pr_number` `integer`
- `pr_url` `text`
- `head_sha` `text`
- `base_branch` `text`
- `state` `text` not null
  - `none`, `branch_created`, `pr_open`, `pr_merged`, `pr_closed`
- `metadata` `jsonb` not null default `'{}'::jsonb`
- `created_at` `timestamptz` not null default `now()`
- `updated_at` `timestamptz` not null default `now()`

Indexes:
- index on `(pr_number)`
- index on `(branch_name)`
- index on `(work_item_id, state)`

### `queue_reconciliations`
Records import/export sync actions.

Columns:
- `id` `uuid` primary key
- `item_id` `text` not null
- `direction` `text` not null
  - `import`, `export`
- `queue_path` `text` not null
- `queue_sha256` `text`
- `db_work_item_id` `uuid` references `work_items(id)`
- `status` `text` not null
  - `applied`, `skipped`, `conflict`, `error`
- `message` `text` not null default `''`
- `created_at` `timestamptz` not null default `now()`

Indexes:
- index on `(item_id, created_at desc)`
- index on `(direction, status, created_at desc)`

## Minimal API Contract
This is an internal API.
It does not need public internet exposure in Phase 1.

### `POST /api/v1/queue/import`
Imports one queue JSON file.

Request body:
```json
{
  "repo_root": "/workspaces/RTLGen",
  "queue_path": "runs/eval_queue/openroad/queued/l2_example.json",
  "source_commit": "abc1234",
  "mode": "upsert"
}
```

Behavior:
- parse queue JSON
- create or update `task_requests` and `work_items`
- record `queue_reconciliations`
- reject conflicting `item_id` / incompatible state transitions

### `POST /api/v1/work-items/{item_id}/lease`
Used by an internal worker to acquire a lease.

Request body:
```json
{
  "machine_key": "eval-desktop-01",
  "capability_filter": {
    "platform": "nangate45",
    "flow": "openroad"
  },
  "lease_seconds": 1800
}
```

Response:
```json
{
  "lease_token": "lease_xxx",
  "expires_at": "2026-03-08T12:00:00Z",
  "work_item": {
    "item_id": "l2_e2e_softmax_macro_tail_v1",
    "input_manifest": {},
    "command_manifest": {},
    "expected_outputs": []
  }
}
```

Alternative mode:
- `POST /api/v1/leases/acquire-next`
- scheduler chooses the next eligible work item for the machine

### `POST /api/v1/leases/{lease_token}/heartbeat`
Extends a live lease.

Request body:
```json
{
  "run_key": "run_l2_e2e_softmax_macro_tail_v1_attempt1",
  "progress": {
    "phase": "run_campaign",
    "command_index": 2,
    "message": "physical sweep running"
  },
  "extend_seconds": 1800
}
```

Behavior:
- update lease expiry
- append `run_events`
- mark machine last seen

### `POST /api/v1/leases/{lease_token}/start-run`
Creates a `runs` row for the leased execution attempt.

Request body:
```json
{
  "run_key": "run_l2_e2e_softmax_macro_tail_v1_attempt1",
  "attempt": 1,
  "executor_type": "internal_worker",
  "container_image": "rtlgen-eval:2026-03-08",
  "checkout_commit": "1141673"
}
```

### `POST /api/v1/runs/{run_key}/events`
Append execution events.

### `POST /api/v1/runs/{run_key}/complete`
Mark run success or failure.

Request body:
```json
{
  "status": "succeeded",
  "result_summary": "campaign completed and artifacts staged",
  "result_payload": {
    "metrics_rows": [],
    "reports": []
  },
  "artifacts": [
    {
      "kind": "report_md",
      "storage_mode": "repo",
      "path": "runs/campaigns/.../report.md"
    }
  ]
}
```

### `POST /api/v1/queue/export/{item_id}`
Writes a DB-backed queue snapshot JSON to the requested queue path.

Request body:
```json
{
  "repo_root": "/workspaces/RTLGen",
  "target_state": "queued",
  "target_path": "runs/eval_queue/openroad/queued/l2_example.json"
}
```

## Lease Model

### Lease acquisition
- only `ready` work items may be leased
- scheduler assigns at most one active lease per work item
- acquisition is transactional
- on successful lease:
  - `work_items.state` becomes `leased`
  - `worker_leases.status` becomes `active`

### Lease duration
Recommended initial values:
- default lease: `30 min`
- heartbeat interval: `5 min`
- stale threshold: `2 x heartbeat interval`

### Lease renewal
- worker must heartbeat before expiry
- each heartbeat may extend lease by up to the configured maximum
- scheduler may deny extension if run is revoked or superseded

### Lease expiration
If lease expires without heartbeat:
- `worker_leases.status = expired`
- `work_items.state` returns to `ready` unless a terminal run status already exists
- scheduler may create a new lease for another machine

### Lease release
Worker may release a lease explicitly when:
- validation fails before execution begins
- machine cannot satisfy the task
- operator cancels the run

Release action:
- `worker_leases.status = released`
- `work_items.state = ready` or `blocked` depending on failure classification

## Scheduler Algorithm
Phase 1 scheduler should stay simple.

### Priority order
Sort candidate work items by:
1. `priority desc`
2. `created_at asc`
3. `item_id asc`

### Eligibility filters
A machine may receive a work item only if:
- `platform` matches
- `flow` matches
- machine is `active`
- task-specific capability constraints are satisfied

### No speculative multi-lease
Do not lease the same item to multiple workers in Phase 1.

## Worker Protocol

### Worker bootstrap
1. register or refresh `worker_machines`
2. request next lease
3. create local checkout/workspace
4. start run
5. execute commands in manifest order
6. emit heartbeats and events
7. stage outputs
8. report completion
9. release lease implicitly through terminal run completion

### Local workspace rules
Internal workers may use transient local workspaces.
They must not commit transient paths into repo-tracked metadata.

### Command execution rules
- execute `task.commands[]` in order
- do not rewrite commands unless task policy allows it
- record command start/end events with exit code
- persist stdout/stderr to transient logs and reference them in `artifacts`

### Result staging rules
Before marking success:
- ensure committed outputs are copied into repo-tracked paths
- ensure `metrics.csv` and queue `result_path` fields do not point to `/tmp/...`
- ensure validator-gated files are present

### Failure classification
Phase 1 worker should classify failure coarsely:
- `infra_failure`
- `validation_failure`
- `flow_failure`
- `artifact_sync_failure`

Detailed reasoning may be delegated to a later triage agent.

## Queue JSON Import Rules

### Import source
The importer reads existing queue JSON files from:
- `runs/eval_queue/openroad/queued/*.json`
- `runs/eval_queue/openroad/evaluated/*.json`

### Identity mapping
Map queue fields as follows:
- queue `item_id` -> `work_items.item_id`
- queue `title` -> `task_requests.title`
- queue `layer` -> `task_requests.layer`, `work_items.layer`
- queue `flow` -> `task_requests.flow`, `work_items.flow`
- queue `priority` -> `task_requests.priority`, `work_items.priority`
- queue `platform` -> `work_items.platform`
- queue `task.inputs` -> `work_items.input_manifest`
- queue `task.commands` -> `work_items.command_manifest`
- queue `task.expected_outputs` -> `work_items.expected_outputs`
- queue `task.acceptance` -> `work_items.acceptance_rules`
- queue path -> `work_items.queue_snapshot_path`

### Queue state mapping
- `queued` file -> `work_items.state = ready` unless DB already has a later state
- `evaluated` file -> `work_items.state = awaiting_review` or `merged` depending on PR linkage and merge status

### Import idempotence
Import must be idempotent.
If the same file content is imported twice:
- no duplicate task request,
- no duplicate work item,
- reconciliation row may still be appended for audit.

### Conflict rules
Import should reject or flag `conflict` if:
- same `item_id` appears with incompatible task payload,
- queue file says `queued` but DB already has terminal state with non-matching identity,
- `evaluated` payload references a different branch or executor than DB-known run without explicit override.

## Queue JSON Export Rules

### Export purpose
Export exists for:
- compatibility with existing evaluator workflows,
- human-readable audit,
- PR publication.

### Export target states
Phase 1 supports exporting:
- `queued`
- `evaluated`

### Export content rules
Exported JSON must preserve current schema shape.
It may add no DB-only fields unless the schema is extended in the repo.

### Export source of truth
When exporting:
- task structure comes from `work_items`
- handoff/result identity comes from latest `runs` and `github_links`
- status comes from DB state

### Evaluated export rule
Do not export `state=evaluated` unless:
- a terminal `runs.status` exists,
- required result identity exists,
- required metrics references exist when `status=ok`.

## GitHub Bridge Contract

### Phase 1 behavior
GitHub bridge only needs to store linkage.
Automatic PR creation can remain optional in Phase 1.

### Required DB linkage
For any evaluator-issued branch or PR, store:
- `repo`
- `branch_name`
- `pr_number`
- `pr_url`
- `head_sha`
- `base_branch`
- link to `work_item_id` and optionally `run_id`

### Merge reconciliation
When a PR is merged:
- update `github_links.state = pr_merged`
- update `work_items.state = merged`
- record merge event in `run_events` or a dedicated reconciliation event

## Internal Worker Execution Recipe
Phase 1 should support existing queue commands directly.

Recommended worker steps:
1. `git clone` or reuse cached repo mirror
2. checkout `source_commit` or current target branch base
3. materialize worktree for the run
4. execute queue commands in order
5. run mandatory validators
6. stage repo-tracked outputs
7. generate evaluated queue snapshot if task completed
8. optionally create branch/commit for publication

This intentionally minimizes new task syntax.

## Migration and Compatibility

### Phase 1 migration rule
No existing queue item format should need to change to start Phase 1.

### Supported coexistence
During migration, these may coexist:
- manual queue authoring in Git
- DB import of that queue
- internal worker lease-based execution
- evaluator PRs from outside the DB

### Reconciliation precedence
If both DB and Git exist for the same `item_id`:
- Git is authoritative for committed evidence files
- DB is authoritative for internal live execution state
- unresolved differences are recorded as reconciliation conflicts, not silently overwritten

## Security and Trust Boundary

### Internal lane
Internal workers may receive DB credentials with least-privilege access:
- lease acquisition
- heartbeat
- run event reporting
- completion reporting

They should not be allowed to mutate unrelated work items.

### External lane
External contributors should not receive DB credentials in Phase 1.
Their path remains:
- task definition
- local execution
- PR submission

## Suggested Initial Tech Choices
These are recommendations, not mandatory constraints.

### Server/runtime
- Python service stack is acceptable for Phase 1 because repo tooling is already Python-heavy.
- Use SQLAlchemy or direct SQL with migrations.
- Use Alembic or equivalent migration tooling.

### DB
- PostgreSQL

### Worker transport
- simple HTTPS JSON API is sufficient in Phase 1
- no message broker is required initially

### Auth
- internal shared token or mTLS inside the trusted environment is sufficient for Phase 1

## Acceptance Criteria
Phase 1 is complete when all of these are true:
- an existing queue item can be imported into DB without loss of task structure,
- an internal worker can lease and execute a DB-backed work item,
- lease expiry and reassignment work,
- a completed run can export a validator-compatible evaluated queue JSON snapshot,
- branch/PR linkage can be recorded in DB,
- Git remains unchanged as the committed evidence format,
- external contributors can continue using the current PR-based path.

## Recommended Build Order
1. create DB schema and migration files
2. implement queue importer
3. implement scheduler and lease acquisition
4. implement worker heartbeat and run reporting
5. implement evaluated queue export
6. implement GitHub linkage reconciliation
7. test coexistence with one real internal evaluation item

## Test Plan

### Unit tests
- queue JSON import mapping
- queue JSON export mapping
- lease acquisition uniqueness
- lease expiration state transition
- run completion updates
- reconciliation conflict detection

### Integration tests
- import a real queued item from `runs/eval_queue/openroad/queued/`
- lease it to a fake worker
- emit run events and heartbeats
- complete run with staged artifacts
- export evaluated JSON
- validate exported JSON shape against repo validators

### Dry-run target
Use one real existing queued item as the first end-to-end dry run.
Prefer a task with a small command surface before a large OpenROAD campaign.

## Deferred to Phase 2+
These are intentionally deferred:
- agent-authored task decomposition in production
- automatic batch PR creation
- policy engine for retuning decisions
- dashboard UI
- public external task-claim system
- richer failure triage automation

## Decision Summary
Phase 1 should not try to be an all-at-once orchestrator.
It should do four things well:
- store work state in DB,
- lease work to internal workers,
- preserve the current queue JSON compatibility surface,
- keep Git and PRs as the evidence boundary.

That is the smallest useful control-plane slice for RTLGen.
