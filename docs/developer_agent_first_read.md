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

8. `docs/abstraction_layering.md`
- generalized layer meaning
- abstraction level vs evaluation mode

9. `docs/two_layer_workflow.md`
- current active Layer 1 / Layer 2 workflow contract

10. `npu/docs/status.md`
- current NPU status and active technical constraints

11. `control_plane/operator_runbook.md`
- current remote evaluation operating model

This set is the default startup context.

## Topic-Specific Baseline Read

After the mandatory set, read only the baselines relevant to the current topic.

Prefer the smallest baseline and architecture set that directly tests the
proposal mechanism first.

Do not default to a broad architecture sweep when a tighter comparison would
answer the proposal question more cleanly.

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
- emitted schedules, traces, or quality-gate artifacts that show where the
  current lowering is leaving performance on the table
- the most recent `analysis_report.md` and `promotion_decision.json` from the
  architecture proposal that exposed the mapper limitation

## Focused Evaluation Set Rule

Every proposal should define:

1. the direct comparison set that is sufficient to test the proposal
   hypothesis
2. which architecture points or variants are intentionally excluded from the
   first evaluation
3. which broader sweep, if any, should happen only as a follow-on evaluation

Default sequencing:
- first-stage evaluation should be minimal and mechanism-focused
- second-stage evaluation may widen to a broader architecture sweep only when
  the focused result is positive, ambiguous, or likely interaction-sensitive

Examples:
- fusion proposal:
  - first-stage: `{non-fused, fused}` on one fixed architecture
  - follow-on: compare the winning fused point against a wider architecture set
- mapper proposal targeting `nm2`:
  - first-stage: `{old mapper, new mapper}` on `nm2`
  - follow-on: re-run `nm1` and `nm2` together only if the local mapper effect
    is established

Reason:
- smaller comparison sets keep the analysis aligned with the stated hypothesis
- they reduce context size and ranking noise during review
- they make it less likely that "campaign winner" is mistaken for
  "proposal outcome"

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

Mapper-specific rule:
- if mapper work is required only to make an approved architecture proposal
  legal or basically runnable, continue the existing proposal
- if an evaluated architecture proposal reached `iterate` because the mapper
  heuristic likely prevented a fair architecture comparison, create or update a
  mapper intake item in `docs/development_items/` first and promote that item
  into its own mapper proposal

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
8. for mapper follow-on work, the triggering proposal/result evidence is linked
   from the intake item or proposal artifacts

Only then move to the direction gate.
