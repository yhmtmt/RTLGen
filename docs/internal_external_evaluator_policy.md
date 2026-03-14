# Internal and External Evaluator Policy

## Purpose
Define how RTLGen should treat two different evaluator populations:
- internal evaluators operating on trusted machines under project control,
- external evaluators contributing compute from outside the local network.

This document complements [agent_control_plane_plan.md](./agent_control_plane_plan.md).

## Why Two Lanes Are Necessary
A single PR-per-evaluation workflow is acceptable for low-volume or untrusted contribution, but it is inefficient for high-volume internal operation.

The project needs both:
- a scalable internal production lane,
- an open but review-gated external contribution lane.

They should share artifact formats and validation rules, but not the same operational control mechanism.

## Policy Summary

### Internal lane
Use a host-side DB-backed control plane.

Characteristics:
- trusted machines,
- lease-based dispatch,
- deterministic workers,
- no PR required for every individual run,
- PRs used only to publish reviewed, decision-relevant result batches.

Current operator documents:
- `control_plane/operator_runbook.md`
- `control_plane/daily_operations.md`
- `control_plane/README.md`

### External lane
Use GitHub-mediated contribution.

Characteristics:
- machine is outside the local network or outside the trust boundary,
- no direct DB or scheduler write access,
- tasks are claimed from public or maintainer-shared task definitions,
- results enter the repo only through PR review,
- provenance must be explicit and validator-clean.

Current operator documents:
- `notes/evaluation_agent_guidance.md`
- `runs/eval_queue/README.md`

## Internal Evaluator Lane

### Intended use
Use the internal lane for:
- routine OpenROAD execution,
- bulk Layer 1 sweeps,
- balanced Layer 2 reruns,
- macro-hardening campaigns,
- retunes and repeated sampling,
- high-frequency operational work.

### Execution model
1. Task is created in the control plane.
2. Scheduler leases it to an internal worker.
3. Worker executes in the standard evaluation container.
4. Outputs are stored transiently outside Git during execution.
5. Result consumer decides whether the run is worth publishing.
6. Only review-worthy outputs are committed and grouped into a PR.

### Branch and PR policy
Do not create one branch per internal micro-run.

Preferred units are:
- one branch per evaluator session,
- one branch per coherent batch,
- one PR per decision-relevant result set.

Examples of acceptable internal PR granularity:
- one Layer 1 module sweep result batch,
- one macro-hardening result,
- one balanced Layer 2 campaign rerun set,
- one candidate-promotion update.

Examples that should usually avoid standalone PRs:
- a single failed run,
- a transient retry,
- a one-row exploratory retune with no decision impact,
- scheduler bookkeeping.

### Internal trust assumptions
Internal workers may have:
- DB access,
- scheduler leases,
- model-cache access,
- object-store or shared-disk access.

They should not require human Git choreography for each run.

## External Evaluator Lane

### Intended use
Use the external lane for:
- volunteer compute,
- collaborators outside the local network,
- ad hoc evaluation contributions,
- situations where direct infrastructure access is undesirable.

### Execution model
1. Maintainer publishes a bounded task definition.
2. External evaluator runs it in the standard environment.
3. Evaluator commits only lightweight outputs.
4. Evaluator opens a PR.
5. Maintainer or review agent validates provenance and artifact correctness.
6. Result is merged only after review.

### Branch and PR policy
For external contributors, PRs are the right submission boundary.

This is because PRs provide:
- trust separation,
- reviewable provenance,
- explicit discussion,
- a natural merge gate.

A branch-per-submission model is acceptable here.
What is not acceptable is using external contributors as direct scheduler clients.

### External trust assumptions
External evaluators should not need:
- direct DB credentials,
- internal scheduler access,
- local network access,
- privileged artifact-store access.

They should only need:
- the repo,
- the documented container environment,
- a task definition,
- validation commands,
- PR submission access.

## Shared Contracts Across Both Lanes
Both lanes must use the same rules for committed artifacts.

Shared requirements:
- lightweight committed outputs only,
- portable `result_path` values,
- validator-clean queue or task metadata,
- explicit source commit and task identity,
- reproducible config and metrics linkage,
- clear result status and summary.

This keeps internal and external evidence comparable.

## Recommended Contribution Unit
For external contributors, the right unit is not “become a queue consumer forever.”
The right unit is:
- claim a bounded task,
- run it,
- submit a result package.

Good external task examples:
- one Layer 1 sweep batch,
- one macro-hardening task,
- one Layer 2 focused rerun item,
- one candidate comparison campaign.

Bad external task examples:
- indefinite polling of the project queue,
- maintaining internal scheduler state,
- directly mutating DB-owned task records.

## Review Policy

### Internal runs
Review is required before merging decision-relevant evidence into Git.
However, review happens after internal scheduling and execution, not before every run begins.

### External runs
Review is required before the project accepts any result into the main repo.
This is mandatory, not optional.

## Suggested PR Threshold
Open a PR when one of these is true:
- result changes a candidate shortlist,
- result changes a default recommendation,
- result closes a queued evaluation item,
- result promotes a candidate to `macro_hardened`,
- result adds a new baseline or campaign report,
- result comes from an external evaluator,
- result changes docs, schemas, or process rules.

Avoid opening a dedicated PR when all of these are true:
- run is internal,
- run is transient or exploratory,
- run does not affect a decision,
- result is better represented as part of a later batch.

## How This Solves the Branch Explosion Problem
The branch explosion happens because branches are currently being used as execution handles.
That should stop for the internal lane.

Recommended change:
- internal lane: branches represent publication batches,
- external lane: branches represent contribution submissions.

This keeps the branch model natural in both cases.

## Relationship to the Queue JSON Files
During migration, queue JSON files can still exist as:
- public task definitions,
- audit snapshots,
- evaluator handoff records.

But they should not remain the sole operational queue for internal work.

For the internal lane:
- DB owns scheduling and leases,
- queue JSON is exported for audit or publication.

For the external lane:
- queue JSON can remain a useful task handoff artifact.

## Recommended First Operational Policy
Adopt this immediately as a project rule:

1. Internal evaluation is scheduler-driven, not PR-driven.
2. External evaluation is PR-driven, not scheduler-credential-driven.
3. Internal micro-runs should be batched before publication.
4. External contributions should be bounded task submissions.
5. Git remains the merge and evidence boundary for both lanes.

## Current Project Baseline

The current repository baseline is:
- internal production evaluation: control-plane driven
- external/manual evaluation: queue/PR driven

Internal lane is no longer a speculative plan.
It is the default trusted-machine operating path for routine evaluation.

## Decision Summary
The current PR-based workflow is not wrong.
It is just serving two different goals at once.

Recommended interpretation:
- keep PR-based submission for external or low-trust compute,
- move internal production evaluation to a DB-backed control plane,
- publish only reviewed, decision-relevant result batches to Git.

That gives the project both openness and scale without conflating execution control with evidence publication.
