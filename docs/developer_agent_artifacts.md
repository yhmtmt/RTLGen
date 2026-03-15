# Developer Agent Artifacts

## Purpose

Define the concrete notebook-side artifacts used by the developer-agent loop.

These artifacts are intentionally lightweight:
- easy to review in Git
- easy to generate from agents
- explicit enough for approval checkpoints

This document complements:
- `docs/developer_agent_loop.md`
- `docs/internal_external_evaluator_policy.md`

## Artifact Set

Use these four artifacts initially:

1. `proposal.json`
- created before implementation
- used for the direction gate

2. `implementation_summary.md`
- created after implementation
- used before the evaluation gate

3. `analysis_report.md`
- created after remote evaluation
- used before the promotion gate

4. `promotion_decision.json`
- concise machine-readable decision artifact
- records `reject`, `iterate`, or `promote`

## 1. proposal.json

### Purpose

Bound a candidate idea before implementation starts.

### Required fields

```json
{
  "proposal_id": "string",
  "created_utc": "ISO-8601 timestamp",
  "created_by": "agent or operator id",
  "layer": "layer1 | layer2 | cross_layer",
  "kind": "circuit | architecture | mapper",
  "title": "short title",
  "hypothesis": "one-paragraph statement",
  "expected_benefit": [
    "string"
  ],
  "risks": [
    "string"
  ],
  "needs_mapper_change": false,
  "required_evaluations": [
    {
      "task_type": "l1_sweep | l2_campaign",
      "objective": "string",
      "cost_class": "low | medium | high"
    }
  ],
  "baseline_refs": [
    "repo path or item id"
  ],
  "knowledge_refs": [
    "paper/doc/note/discussion reference"
  ]
}
```

### Example

```json
{
  "proposal_id": "prop_l2_softmax_tile_fusion_v1",
  "created_utc": "2026-03-15T00:00:00Z",
  "created_by": "developer_agent",
  "layer": "layer2",
  "kind": "architecture",
  "title": "Softmax-tail fused tile path",
  "hypothesis": "Fusing the softmax-tail path into a specialized tile should reduce memory traffic and improve latency for imported softmax workloads.",
  "expected_benefit": [
    "lower model latency",
    "lower SRAM traffic"
  ],
  "risks": [
    "may require new mapper legality rules",
    "could increase area"
  ],
  "needs_mapper_change": true,
  "required_evaluations": [
    {
      "task_type": "l2_campaign",
      "objective": "balanced",
      "cost_class": "high"
    }
  ],
  "baseline_refs": [
    "runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1"
  ],
  "knowledge_refs": [
    "paper:softmax-acceleration-2024",
    "discussion:2026-03-15-user-session"
  ]
}
```

## 2. implementation_summary.md

### Purpose

Summarize what changed before remote evaluation is approved.

### Required sections

```md
# Implementation Summary

## Proposal
- `proposal_id`
- short title

## Scope
- what changed
- what did not change

## Files Changed
- repo paths

## Local Validation
- commands run
- pass/fail summary

## Evaluation Request
- requested remote tasks
- cost class
- baseline to compare against

## Risks
- remaining technical risks
```

## 3. analysis_report.md

### Purpose

Summarize evaluated evidence for a promotion decision.

### Required sections

```md
# Analysis Report

## Candidate
- `proposal_id`
- `candidate_id`

## Evaluations Consumed
- work item ids
- run keys
- source commit

## Baseline Comparison
- what baseline was used
- key deltas

## Result
- win / loss / mixed
- confidence level

## Failures and Caveats
- flow failures
- validation anomalies
- mapper limitations

## Recommendation
- reject / iterate / promote
- short reason
```

## 4. promotion_decision.json

### Purpose

Provide a small machine-readable decision record after analysis.

### Required fields

```json
{
  "proposal_id": "string",
  "candidate_id": "string",
  "decision": "reject | iterate | promote",
  "reason": "short explanation",
  "evidence_refs": [
    "work item id, run key, PR, or repo path"
  ],
  "next_action": "string",
  "requires_human_approval": true
}
```

### Example

```json
{
  "proposal_id": "prop_l2_softmax_tile_fusion_v1",
  "candidate_id": "cand_l2_softmax_tile_fusion_v1_r2",
  "decision": "iterate",
  "reason": "Latency improved but mapper spill behavior is still unstable on one workload.",
  "evidence_refs": [
    "item:l2_softmax_tile_fusion_20260315",
    "run:l2_softmax_tile_fusion_20260315_run_abcd1234",
    "runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1__l2_softmax_tile_fusion_20260315/report.md"
  ],
  "next_action": "tighten mapper legality checks and rerun the same campaign",
  "requires_human_approval": true
}
```

## Placement

Initial recommendation:
- keep these artifacts in the notebook-side working branch
- store them under a small dedicated directory such as:
  - `docs/developer_loop/`
  - or another future notebook-local workflow directory

Do not put them in the evaluator execution area.

## Initial Rule

Do not add database schema for these artifacts yet.

Initial implementation should keep them:
- file-based
- reviewable
- notebook-local

Only move them into a DB workflow if the notebook-side creative loop becomes
operationally heavy enough to justify it.
