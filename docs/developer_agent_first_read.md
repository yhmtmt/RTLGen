# Developer Agent First Read

## Purpose

Define the minimum context a notebook-side developer agent must ingest at the
start of a new session before proposing work, choosing a `proposal_id`, or
editing code.

This is the bounded startup context for the internal trusted lane.

Related documents:
- `docs/developer_agent_loop.md`
- `docs/developer_agent_artifacts.md`
- `docs/developer_agent_orchestration.md`
- `docs/internal_external_evaluator_policy.md`

## Startup Rule

Before creating or updating a proposal, the developer agent should:
1. read the mandatory first-read set in order,
2. select only the topic-relevant baselines,
3. inspect the preliminary intake backlog in `docs/development_items/`,
4. inspect existing open proposal directories for overlap,
5. then choose or update the `proposal_id`.

Do not start from old session residue or broad repo-wide grep alone.

## Mandatory First-Read Set

Read these in order for every new developer-agent session:

1. `README.md`
- repo scope
- layer split
- control-plane entrypoints

2. `docs/structure.md`
- doc roles
- canonical precedence

3. `docs/internal_external_evaluator_policy.md`
- internal vs external evaluation lane boundaries

4. `docs/developer_agent_loop.md`
- role split
- stage model
- approval gates

5. `docs/developer_agent_artifacts.md`
- required proposal/analysis/promotion artifacts

6. `docs/development_items/README.md`
- intake backlog structure and item-id rule

7. `docs/developer_agent_orchestration.md`
- practical notebook-side working procedure

8. `docs/two_layer_workflow.md`
- Layer 1 / Layer 2 contract

9. `npu/docs/status.md`
- current NPU status and active technical constraints

10. `control_plane/operator_runbook.md`
- current remote evaluation operating model

This set is the default startup context.

## Topic-Specific Baseline Read

After the mandatory set, read only the baselines relevant to the current topic.

### For Layer 1 proposals

Prefer:
- `docs/layer1_circuit_workflow.md`
- relevant `runs/designs/**/metrics.csv`
- relevant `runs/candidates/**`
- relevant promoted review artifacts

### For Layer 2 proposals

Prefer:
- `npu/docs/workflow.md`
- relevant `runs/campaigns/**/report.md`
- relevant `runs/campaigns/**/summary.csv`
- relevant `runs/campaigns/**/best_point.json`
- relevant promoted review artifacts

### For mapper proposals

Prefer:
- `npu/docs/workflow.md`
- current Layer 2 campaign reports showing mapper bottlenecks
- failing or constrained evaluation evidence tied to the architecture change

## Existing Proposal Check

Before choosing a new `proposal_id`, inspect:
- `docs/development_items/index.md`
- relevant `docs/development_items/items/<item_id>.md`
- `docs/developer_loop/README.md`
- existing directories under `docs/developer_loop/`

Goal:
- avoid duplicate proposals,
- continue an existing proposal when appropriate,
- increment the version suffix only when the direction is materially new.

## Proposal ID Rule

Use:

```text
prop_<layer>_<topic>_<change>_vN
```

Examples:
- `prop_l1_prefix_fanout_balance_v1`
- `prop_l2_softmax_tile_fusion_v1`
- `prop_l2_mapper_softmax_tiling_v2`

Rules:
- `layer` should be `l1`, `l2`, or `cross`
- `topic` should identify the workload, block, or architecture family
- `change` should identify the proposed mechanism
- `vN` increments only when the proposal direction changes enough that it
  should not overwrite the previous one

## Context To Ingest From The User

If the user provides new direction, treat these as first-class inputs:
- papers
- design discussion
- explicit target metrics
- constraints on area, runtime, or architecture complexity
- approval conditions for spending remote evaluation budget

Record those references in:
- `proposal.json`
- `design_brief.md`

## What Not To Ingest By Default

Do not bulk-ingest these at session start:
- all of `notes/`
- archived control-plane proof logs
- every campaign directory in `runs/campaigns/`
- every proposal directory in `docs/developer_loop/`
- old session handoff artifacts

Reason:
- they add noise,
- increase drift risk,
- and weaken proposal scoping.

Only pull them in when directly relevant to the current candidate.

## Session Startup Checklist

Before the first code change, confirm:

1. mandatory first-read set is covered
2. topic-relevant baselines are selected
3. relevant intake items are checked in `docs/development_items/`
4. overlapping proposal directories are checked
5. `proposal_id` is chosen or reused
6. `docs/developer_loop/<proposal_id>/` exists
7. `proposal.json` and `design_brief.md` are initialized

Only then move to the direction gate.
