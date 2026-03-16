# Developer Agent Loop

## Purpose

Define the notebook-side autonomous development loop that sits above the
existing control-plane execution system.

This loop is for:
- proposing new Layer 1 circuits
- proposing new Layer 2 architectures
- introducing required mapper changes
- requesting remote evaluation
- analyzing results
- preparing promotion decisions

It is not the evaluator-worker loop.
The evaluator desktop remains a deterministic execution role.

## Scope

This document covers the internal trusted-machine lane only.

Related documents:
- `docs/internal_external_evaluator_policy.md`
- `docs/developer_agent_first_read.md`
- `docs/developer_agent_artifacts.md`
- `docs/developer_agent_orchestration.md`
- `control_plane/operator_runbook.md`
- `control_plane/remote_operator_workflow.md`
- `docs/two_layer_workflow.md`

## Role Split

Human:
- provides knowledge bases, papers, and discussion
- approves direction, evaluation spend, and final promotion

Notebook developer agents:
- read knowledge bases and prior results
- implement L1/L2/mapper changes
- generate evaluation tasks
- analyze results
- prepare promotion recommendations

Evaluator desktop:
- consumes queued work
- executes deterministic evaluation tasks
- does not invent new designs or policies

## Design Principle

Keep invention and judgment on the notebook.
Keep execution on the evaluator.

In practice:
- creative work stays notebook-local
- evaluation work goes through the control plane
- Git remains the reviewed evidence boundary

## Session Start

Before a notebook-side developer agent chooses a new proposal direction or
`proposal_id`, it should ingest the bounded startup context defined in:
- `docs/developer_agent_first_read.md`

## Agent Roles

### 1. Research/Planning Agent

Inputs:
- papers
- your discussion
- prior evaluation results
- repository notes and docs

Outputs:
- `design_brief.md`
- bounded hypotheses
- candidate directions

### 2. Layer 1 Circuit Agent

Responsibility:
- propose new RTLGen circuit structures, generator options, or parameter spaces

Outputs:
- code/config changes
- local smoke results
- Layer 1 evaluation requests

### 3. Layer 2 Architecture Agent

Responsibility:
- propose new NPU architecture points, templates, or campaign variants

Outputs:
- architecture/config changes
- local smoke results
- Layer 2 evaluation requests

### 4. Mapping Agent

Responsibility:
- implement mapper/scheduler/legality changes required by a new architecture

Trigger this role only when the L2 proposal cannot be evaluated with the
current mapping pipeline.

### 5. Evaluation Analyst Agent

Responsibility:
- compare finished results against baselines
- decide whether to reject, iterate, or promote

Outputs:
- `analysis_report.md`
- `promotion_decision.json`

## Task Loop

### Stage 1. Knowledge Ingest

Goal:
- turn raw knowledge input into bounded engineering hypotheses

Outputs:
- `design_brief.md`
- `proposal.json`

Concrete artifact schema:
- `docs/developer_agent_artifacts.md`

`proposal.json` should include:
- `proposal_id`
- `layer`
- `hypothesis`
- `expected_benefit`
- `risk_level`
- `required_evaluations`
- `needs_mapper_change`

### Stage 2. Direction Gate

Human approval required.

Approve:
- which candidate directions are worth implementation

Reject:
- vague, unbounded, or unjustified proposals

This keeps the agent from drifting into large speculative branches.

### Stage 3. Implementation

Goal:
- turn the approved proposal into runnable code/config/test changes

Possible subtasks:
- `l1_implementation`
- `l2_implementation`
- `mapper_implementation`

Required outputs:
- implementation diff
- `implementation_summary.md`
- local smoke/regression results

### Stage 4. Quality Precheck

This stage is required when the proposal can affect:
- numerical semantics
- quantization behavior
- output tensors
- model-quality outcomes

Examples:
- activation-function changes
- softmax/layernorm changes
- mapper changes that can alter terminal outputs

Goal:
- prove the candidate is not only structurally valid, but also numerically
  acceptable before expensive remote PPA spend

Required output:
- `quality_gate.md`

This is not an extra human approval gate by default.
It is a mandatory technical gate for numerically sensitive proposals.

### Stage 5. Evaluation Gate

Human approval required.

Approve:
- which implemented candidates deserve remote evaluation
- which ones are worth Layer 1 spend
- which ones are worth Layer 2 campaign spend

This is the compute-budget gate.

### Stage 6. Queue Generation

Notebook agents generate DB-native work items through the control plane.

Required metadata per work item:
- `source_commit`
- `candidate_id`
- `hypothesis_id`
- `task_type`
- `expected_outputs`
- `required_submodules`
- evaluation objective or comparison target

### Stage 7. Remote Evaluation

Evaluator daemon:
- leases the task
- executes it in a clean disposable worktree
- syncs allowlisted evidence back to the notebook

This stage is already implemented by the control plane.

### Stage 8. Result Analysis

Notebook analysis agent reads:
- Layer 1 metrics
- Layer 2 campaign reports
- baselines
- prior winning points
- failure classifications

Required outputs:
- `analysis_report.md`
- `promotion_decision.json`

Concrete artifact schema:
- `docs/developer_agent_artifacts.md`

`promotion_decision.json` should include:
- `candidate_id`
- `decision`
  - `reject`
  - `iterate`
  - `promote`
- `evidence_refs`
- `reason`
- `next_action`

### Stage 9. Promotion Gate

Human approval required.

Approve:
- merge/publish the candidate
- or authorize another iteration cycle

This is the final design-authority gate.

### Stage 10. Promotion / Merge

If approved:
- submit or refresh the PR
- review the evidence
- merge the accepted result batch

## Required Checkpoints

Use exactly these three approval points initially:

1. `Direction Gate`
- before implementation

2. `Evaluation Gate`
- before expensive remote evaluation

3. `Promotion Gate`
- before merge/publication

Everything else should be autonomous.

## Task Classes

These are the logical notebook-side task classes:
- `knowledge_digest`
- `design_proposal`
- `l1_implementation`
- `l2_implementation`
- `mapper_implementation`
- `eval_request_l1`
- `eval_request_l2`
- `result_analysis`
- `promotion_request`

Not all of these need DB-backed scheduling immediately.

Current recommended split:
- notebook-local agent orchestration for creative tasks
- control-plane scheduling only for deterministic remote evaluation

## Mapper Trigger Rules

Do not spawn mapper work automatically for every L2 idea.

Spawn a mapper subtask only when:
- legality checks fail
- SRAM-fit assumptions break
- tiling/splitting is required
- schedule semantics must change
- new architecture semantics are not representable in the current mapper

## Authority Rules

Developer agents may:
- read docs, notes, and papers
- edit code/config/tests
- run local smoke checks
- enqueue evaluation tasks
- analyze results
- prepare PRs

Developer agents should not do without approval:
- broad direction changes
- expensive evaluation campaigns beyond policy
- final promotion/merge of new design directions

## Minimal Initial Implementation

Do not push the entire notebook-side creative loop into the control plane yet.

Initial implementation should be:
- notebook-local agent workflow for proposal/implementation/analysis
- control plane used only for remote execution and evidence return
- explicit artifacts for each checkpoint
- human approval at the three gates above

This keeps the existing evaluator system simple while allowing autonomous
development to scale on the notebook side.

Practical notebook-side procedure:
- `docs/developer_agent_orchestration.md`
