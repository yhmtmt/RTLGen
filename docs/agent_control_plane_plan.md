# Agent Control Plane Plan

## Purpose
Define a scalable control-plane architecture for RTLGen that:
- keeps the current GitHub PR-based evaluation workflow working,
- moves operational coordination outside the devcontainers,
- reduces unnecessary Codex-agent invocations and token usage,
- supports dedicated Layer 1 and Layer 2 task generators/consumers,
- preserves Git as the source of reproducible experiment artifacts.

This document is a plan, not an implementation claim.

## Problem Statement
The current workflow is effective but operationally coarse:
- development and evaluation both happen inside similar devcontainers,
- heavy evaluation is communicated by committing JSON queue items,
- evaluators poll Git state, create branches, run flows, and open PRs,
- the queue itself doubles as both execution control and audit trail.

That has three costs:
1. too much state is encoded indirectly in Git commits and PR text,
2. evaluator agents remain active longer than necessary,
3. Layer 1 and Layer 2 orchestration logic is not yet separated into stable services.

## Design Goals
1. Keep Git and PRs as the reproducible artifact and review boundary.
2. Move scheduling, leases, retries, state transitions, and machine assignment to a host-side control plane.
3. Use a database for operational state, not for final scientific provenance.
4. Invoke Codex agents only where reasoning is needed.
5. Run deterministic evaluation steps without a persistent Codex loop.
6. Add explicit Layer 1 and Layer 2 generator/consumer roles.
7. Preserve compatibility with the existing `runs/eval_queue/openroad/queued -> evaluated` exchange during migration.

## Non-Goals
- Replacing GitHub PR review with an internal approval UI.
- Hiding experiment definitions inside the database only.
- Treating evaluator machines as mutable snowflakes.
- Running OpenROAD directly from a long-lived chat agent session.

## Core Principle
Split the system into two planes:
- Control plane: host-side services, database, scheduler, leases, retries, policy, machine inventory, task decomposition, and agent invocation control.
- Evidence plane: repo-tracked configs, manifests, metrics rows, reports, queue snapshots, and PRs.

Operational truth lives in the control plane.
Reproducible scientific truth lives in Git.

## Recommended Architecture

### 1. Host-Side Control Plane
Run these services outside devcontainers, on the host or on a small orchestration node:
- `api-server`: receives task requests, exposes task/run status, and triggers generators/consumers.
- `scheduler`: owns prioritization, evaluator-machine assignment, retry policy, and backpressure.
- `worker-launcher`: starts deterministic evaluation jobs in the evaluation container or on the evaluation desktop.
- `github-bridge`: opens PRs, posts status/comments, syncs queue snapshots, and links DB runs to commits.
- `artifact-sync`: copies approved outputs from ephemeral workspaces into repo-tracked locations before PR creation.
- `agent-runner`: invokes Codex only for reasoning steps.

Recommended persistence:
- PostgreSQL for control-plane state.
- Local disk or object storage for transient logs and large non-committed run artifacts.
- Git repository for committed lightweight artifacts.

### 2. Containers Become Execution Environments
Keep the current devcontainer image, but change its role:
- development container: code authoring, local validation, design changes.
- evaluation container: deterministic task execution environment launched by the control plane.

The container should not be the scheduler.
The container should not be the authoritative queue.
The container should be an execution target.

### 3. DB-First Operational Model
Use the database for:
- task submission,
- task state transitions,
- worker leases,
- machine capabilities,
- retry counts,
- task lineage,
- agent invocation records,
- result ingestion status,
- PR linkage.

Use Git for:
- experiment definitions that must be reviewed,
- candidate manifests,
- campaign configs,
- committed metrics and reports,
- queue snapshots for human-readable audit and compatibility.

## Proposed Agent Taxonomy

### A. Development Agent
Purpose:
- change algorithms, generators, schemas, docs, and campaign definitions.

Runs when:
- a human requests design changes or analysis that requires code edits.

Should not:
- stay alive to wait for OpenROAD completion.

### B. Evaluation Executor
Purpose:
- run deterministic commands already defined by a task.

This is preferably not a Codex agent.
It should be a plain worker process driven by the control plane.

Responsibilities:
- materialize source checkout,
- fetch external model artifacts,
- execute validation and OpenROAD commands,
- collect results,
- write transient logs,
- hand outputs to artifact-sync.

### C. Evaluation Triage Agent
Purpose:
- reason about failures or ambiguous outcomes.

Invoke only when:
- validation fails unexpectedly,
- OpenROAD result classification is unclear,
- retuning is permitted by policy,
- a PR review comment must be synthesized from observed artifacts.

### D. Layer 1 Task Generator Agent
Purpose:
- transform Layer 1 requests into concrete sweep tasks.

Inputs:
- module family,
- candidate configs,
- PDK,
- sweep policy,
- constraints from Layer 2 feedback.

Outputs:
- normalized Layer 1 work items,
- queue snapshot JSON for Git compatibility,
- expected outputs and acceptance gates.

### E. Layer 1 Result Consumer Agent
Purpose:
- ingest Layer 1 results and decide next action.

Responsibilities:
- validate metrics rows,
- update candidate status proposals,
- detect domination and shortlist survivors,
- request macro-hardening when a wrapper-level candidate must be promoted,
- emit follow-on Layer 1 or Layer 2 tasks.

### F. Layer 2 Task Generator Agent
Purpose:
- generate model-level NPU evaluation tasks.

Inputs:
- model sets,
- architecture search space,
- candidate module manifests from Layer 1,
- objective profiles,
- policy constraints.

Outputs:
- campaign variants,
- architecture-point selections,
- physical rerun requests,
- queue snapshot JSON for evaluator compatibility.

### G. Layer 2 Result Consumer Agent
Purpose:
- ingest campaign results and produce architecture decisions.

Responsibilities:
- validate campaign completeness,
- detect unbalanced rerun counts,
- compare architecture points under the configured objective,
- identify when Layer 2 feedback should trigger new Layer 1 work,
- draft recommendation summaries.

### H. PR Review Agent
Purpose:
- review evaluator-issued PRs for metadata correctness, path portability, missing assets, and regressions.

This can remain Codex-based because it is reasoning-heavy but short-lived.

## When Codex Should Be Invoked
Codex should be used for:
- task decomposition that requires reading repo intent,
- failure triage,
- result interpretation,
- PR review,
- generating or refining queue/task definitions,
- producing human-facing summaries.

Codex should not be used for:
- polling queues,
- waiting on OpenROAD,
- copying files,
- running standard validation commands,
- fetching models,
- creating branches for deterministic jobs,
- executing a fixed campaign command that the control plane already knows.

This is the main token-reduction rule.

## Operational Entities
Recommended database tables or equivalent entities:

### `task_templates`
Reusable task blueprints.
Examples:
- Layer 1 sweep template,
- macro-hardening template,
- Layer 2 campaign rerun template.

### `task_requests`
Human- or agent-issued requests.
Examples:
- “evaluate softmax macro in Layer 2”,
- “rerun flat mode 10 times”,
- “promote candidate X to macro_hardened”.

### `work_items`
Concrete executable units created from task requests.

Fields should include:
- `work_item_id`
- `layer` (`l1`, `l2`, `meta`)
- `task_type`
- `priority`
- `source_commit`
- `requested_by`
- `policy_id`
- `input_manifest`
- `expected_outputs`
- `state`
- `lease_owner`
- `lease_expires_at`

### `runs`
Actual execution attempts.

Fields should include:
- `run_id`
- `work_item_id`
- `attempt`
- `executor_type` (`worker`, `agent-assisted-worker`)
- `machine_id`
- `container_image`
- `branch_name`
- `started_at`
- `completed_at`
- `status`
- `result_summary`

### `artifacts`
Transient and committed artifact references.

Fields should include:
- `artifact_id`
- `run_id`
- `kind` (`metrics_csv`, `report_md`, `macro_manifest`, `queue_snapshot`, `log_bundle`)
- `storage_mode` (`transient`, `repo`, `object_store`)
- `path`
- `sha256`

### `candidates`
Layer 1 and cross-layer candidate tracking.

Fields should include:
- `candidate_id`
- `pdk`
- `module_family`
- `config_hash`
- `evaluation_scope`
- `status`
- `source_metrics_row`
- `macro_manifest_path`

### `campaign_decisions`
Layer 2 result summaries and recommendation state.

Fields should include:
- `campaign_id`
- `objective_profile`
- `winner_arch_id`
- `winner_module_set`
- `evidence_report_path`
- `decision_status`

## State Machine

### Work item states
- `draft`
- `ready`
- `leased`
- `running`
- `artifact_sync`
- `awaiting_review`
- `merged`
- `failed`
- `blocked`
- `superseded`

### Key rule
No evaluator machine should discover work by scanning Git alone.
It should lease work from the control plane.
Git queue files become exported snapshots, not the primary lock mechanism.

## Git Queue Compatibility Model
The current JSON queue should be preserved during migration.

Recommended approach:
1. Authoritative queue state is stored in DB.
2. Control plane exports compatible JSON snapshots into:
   - `runs/eval_queue/openroad/queued/`
   - `runs/eval_queue/openroad/evaluated/`
3. Evaluator PRs still commit the evaluated item for audit and backward compatibility.
4. The DB stores the canonical run state and PR linkage.

This gives three benefits:
- old repo workflows still work,
- humans can still inspect queue items in Git,
- operational scheduling no longer depends on Git polling.

## Execution Flow

### Flow A: Human requests a new evaluation
1. Human or development agent submits a task request to the control plane.
2. Appropriate generator agent expands it into one or more work items.
3. Scheduler assigns work items to eligible evaluator machines.
4. Worker-launcher starts evaluation container jobs.
5. Deterministic executor runs validations and OpenROAD.
6. Artifact-sync copies lightweight outputs into repo-tracked paths.
7. GitHub bridge creates or updates an evaluator branch and PR.
8. PR review agent or human reviews results.
9. On merge, result consumer ingests the merged artifacts and updates DB state.

### Flow B: Layer 1 feedback into Layer 2
1. Layer 1 result consumer observes a shortlisted or macro-hardened candidate.
2. It emits a Layer 2 task request referencing candidate manifests.
3. Layer 2 generator creates campaign variants using that candidate set.
4. Scheduler dispatches campaign reruns.
5. Layer 2 result consumer compares campaign outcomes and records the recommendation.

### Flow C: Layer 2 feedback into Layer 1
1. Layer 2 result consumer detects a bottleneck or sensitivity.
2. It emits a targeted Layer 1 request.
Examples:
- “softmax dominates tail latency for row_bytes=4”,
- “nm2 only wins when GEMM split amortizes event overhead”,
- “macro-harden candidate X before making hierarchical claims”.
3. Layer 1 generator constrains the sweep to the narrowest useful search region.

## Layer 1 Generator/Consumer Design

### Generator responsibilities
- read current candidate manifest and pending feedback,
- choose sweep dimensions and bounds,
- materialize configs and queue-compatible task definitions,
- reject redundant or dominated requests.

### Consumer responsibilities
- verify `metrics.csv` integrity,
- classify result quality:
  - valid,
  - flow issue,
  - design issue,
  - data issue,
- maintain shortlist status,
- trigger macro-hardening only for candidates that survive module-level comparison,
- produce machine-readable handoff to Layer 2.

### Output contract
The Layer 1 consumer should publish:
- shortlist candidates,
- reason for selection,
- rejected candidates and reason,
- whether macro-hardening is required,
- Layer 2 handoff payload.

## Layer 2 Generator/Consumer Design

### Generator responsibilities
- choose model sets,
- choose architecture parameter combinations,
- choose module candidate substitutions from Layer 1,
- enforce balanced rerun policy,
- emit minimal campaign deltas rather than ad hoc one-off tasks.

### Consumer responsibilities
- validate campaign completeness,
- aggregate balanced results only,
- rank points under named objective profiles,
- issue clear decisions:
  - new default,
  - needs rerun,
  - send feedback to Layer 1,
  - blocked by unsupported op or missing macro.

### Output contract
The Layer 2 consumer should publish:
- winning architecture point,
- winning module set,
- evidence report path,
- residual risks,
- requests back to Layer 1 when appropriate.

## Control Policy

### Scheduling policy
Recommended priority order:
1. merge-blocking reruns,
2. candidate-promotion tasks,
3. decision-closing Layer 2 campaigns,
4. exploratory sweeps,
5. speculative broad searches.

### Retry policy
- deterministic validation failure: no automatic retry; escalate to triage agent.
- transient machine failure: automatic retry on another machine.
- OpenROAD QoR miss on a tunable task: retry only if task policy explicitly allows retuning.

### Machine policy
Track machine capabilities in DB:
- OpenROAD version,
- CPU count,
- RAM,
- disk budget,
- model cache availability,
- whether large local caches are warm.

The scheduler should place jobs based on these capabilities, not on ad hoc human memory.

## Artifact Policy

### Commit to Git
- configs,
- manifests,
- generated RTL when part of the experiment contract,
- `metrics.csv`, report summaries, campaign outputs,
- queue snapshots,
- documentation,
- candidate and decision manifests.

### Keep outside Git
- large logs,
- temporary work directories,
- DEF/GDS unless explicitly chosen as a release artifact,
- transient fetched models,
- executor-private scratch outputs.

### Provenance rule
Every committed result must be reconstructible from:
- source commit,
- work item input manifest,
- run command set,
- committed metrics/report rows,
- linked PR.

## Why DB Outside Containers Is Correct
This is the main architectural recommendation.

### Benefits
- lower token use because agents do not poll or hold conversational state while jobs run,
- fewer live Codex sessions because deterministic workers can execute directly,
- better leases and retries,
- machine inventory and scheduling become explicit,
- easier support for multiple evaluator desktops or cloud runners,
- easier addition of Layer 1 and Layer 2 autonomous generators/consumers.

### Tradeoff
You now operate another service stack.
That is acceptable because the current queue already behaves like a lightweight workflow engine, but without first-class leases, retries, or structured state.

## Migration Plan

### Phase 0: Documented current-state discipline
Keep current Git queue, evaluator PRs, and manuals.
Add this plan only.

### Phase 1: Shadow control plane
Build the host-side DB and scheduler in shadow mode.
- ingest current queue JSON,
- mirror states into DB,
- do not change evaluator behavior yet,
- prove that DB state matches Git state.

### Phase 2: Lease-based dispatch
Move evaluator task pickup from Git polling to DB leases.
- control plane still exports queue JSON snapshots,
- evaluator workers receive leased tasks from the host service,
- PR outputs remain unchanged.

### Phase 3: Deterministic worker split
Replace persistent evaluator agents with worker processes for standard tasks.
- Codex only for triage and review,
- control plane creates branches and PRs,
- workers run task recipes non-interactively.

### Phase 4: Add Layer 1/Layer 2 generator-consumer agents
Introduce the four additional reasoning roles:
- Layer 1 generator,
- Layer 1 consumer,
- Layer 2 generator,
- Layer 2 consumer.

At this phase, the system becomes policy-driven rather than purely queue-file-driven.

### Phase 5: Optional DB-primary UI
If needed, add a small dashboard or CLI.
Git remains the evidence plane regardless.

## First Concrete Implementation Slice
Recommended first slice, in order:
1. define DB schema for `task_requests`, `work_items`, `runs`, `artifacts`, `candidates`, and `campaign_decisions`;
2. build an importer/exporter between DB state and `runs/eval_queue/openroad/*.json`;
3. add lease semantics and worker assignment;
4. add a deterministic evaluator worker that can execute existing queue `task.commands[]` without Codex;
5. add GitHub bridge for branch/PR creation;
6. add Layer 1 and Layer 2 generator/consumer agents on top of that stable base.

This order matters.
Do not start with autonomous agents before the control plane owns state and leases.

## Recommended Repository Boundaries
Without changing current files yet, the likely future implementation split is:
- `control_plane/`
  - API server
  - scheduler
  - DB models
  - GitHub bridge
  - worker launcher
- `agents/`
  - `layer1_generator`
  - `layer1_consumer`
  - `layer2_generator`
  - `layer2_consumer`
  - `eval_triage`
  - `pr_review`
- existing repo areas remain the evidence plane.

## Decision Summary
Recommended scheme:
- keep the current repo queue and PR review model as the external audit surface,
- move task coordination and leases to a host-side DB-backed control plane,
- run deterministic evaluation with plain workers, not long-lived Codex sessions,
- add Layer 1 and Layer 2 generator/consumer agents only after the control plane is stable,
- use Git for reproducibility and DB for operations.

That is the cleanest path to lower token cost, fewer active agents, clearer state management, and scalable two-layer experimentation.
