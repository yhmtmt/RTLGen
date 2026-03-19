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

Use these artifacts initially:

1. `proposal.json`
- created before implementation
- used for the direction gate

2. `implementation_summary.md`
- created after implementation
- used before the quality precheck and evaluation gate

3. `quality_gate.md`
- required for proposals that can affect numerical semantics, quantization
  behavior, output tensors, or model-quality outcomes
- created after implementation and local quality checks
- required before the evaluation gate for those proposals

4. `analysis_report.md`
- created after remote evaluation
- used before the promotion gate

5. `promotion_decision.json`
- concise machine-readable decision artifact
- records `reject`, `iterate`, or `promote`

## 1. proposal.json

### Purpose

Bound a candidate idea before implementation starts.

The proposal should force the agent to answer:
- what is the minimum comparison set that directly proves or falsifies the
  hypothesis?
- what broader sweep is intentionally deferred until after that focused test?

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
  "direct_comparison": {
    "primary_question": "the smallest comparison that directly tests the hypothesis",
    "include": [
      "variant or architecture point"
    ],
    "exclude": [
      "broader points intentionally excluded from first-stage evaluation"
    ],
    "follow_on_broad_sweep": [
      "optional wider evaluation to run after the focused comparison"
    ]
  },
  "expected_benefit": [
    "string"
  ],
  "risks": [
    "string"
  ],
  "needs_mapper_change": false,
  "required_evaluations": [
    {
      "task_type": "local_quality_precheck | l1_sweep | l2_campaign",
      "evaluation_mode": "measurement_only | baseline_refresh | paired_comparison | broad_ranking",
      "objective": "string",
      "cost_class": "low | medium | high",
      "depends_on_item_ids": [
        "optional prerequisite developer-loop item ids"
      ],
      "requires_merged_inputs": false,
      "requires_materialized_refs": false,
      "expected_result": {
        "direction": "better_than_historical | worse_than_historical | same_as_historical | unknown",
        "reason": "why this outcome is expected"
      }
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
  "direct_comparison": {
    "primary_question": "Does fused output improve the softmax-tail path on the chosen baseline architecture?",
    "include": [
      "nm1 non-fused baseline",
      "nm1 fused candidate"
    ],
    "exclude": [
      "nm2 points during the first-stage fusion proof"
    ],
    "follow_on_broad_sweep": [
      "compare the accepted fused point against a wider nm1/nm2 architecture set"
    ]
  },
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
      "task_type": "local_quality_precheck",
      "evaluation_mode": "measurement_only",
      "objective": "quality_guard",
      "cost_class": "low",
      "depends_on_item_ids": [],
      "requires_merged_inputs": false,
      "requires_materialized_refs": false,
      "expected_result": {
        "direction": "same_as_historical",
        "reason": "quality prechecks should preserve accepted model outputs"
      }
    },
    {
      "task_type": "l2_campaign",
      "evaluation_mode": "paired_comparison",
      "objective": "balanced",
      "cost_class": "high",
      "depends_on_item_ids": [
        "l2_prop_l2_softmax_tile_fusion_v1_nm1_measurement_r1"
      ],
      "requires_merged_inputs": true,
      "requires_materialized_refs": true,
      "expected_result": {
        "direction": "better_than_historical",
        "reason": "the fused candidate is expected to improve the focused baseline"
      }
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

`direct_comparison` exists to keep the first remote evaluation aligned with the
proposal's causal question. For new proposals:
- use the smallest comparison set that can validate the mechanism
- exclude architecture points that only add ranking noise to the first-stage
  decision
- record broader sweeps as follow-on work instead of mixing them into the
  primary proof by default

`required_evaluations[*].evaluation_mode` exists because not every item should
emit a win/lose proposal judgment:
- `measurement_only`: record metrics for named points; no proposal assessment
- `baseline_refresh`: recompute a historical reference point under a new
  contract, toolchain, or benchmark; historical deltas are context, not a loss
- `paired_comparison`: compare a candidate against a named refreshed or
  accepted baseline and emit the focused proposal outcome
- `broad_ranking`: run a wider sweep and serialize ranking separately from the
  focused proposal question

`required_evaluations[*].expected_result` exists because some valid items are
expected to look worse than older historical runs. Example:
- a corrected event contract may make a refreshed non-fused baseline slower
  than an older historical report
- that should be marked as expected when the measured shift matches the stated
  reason

`depends_on_item_ids` and the two `requires_*` flags exist because some items
consume prior developer-loop evidence rather than only historical baselines:
- use `depends_on_item_ids` when an item depends on an earlier measurement or
  refreshed-baseline item
- set `requires_merged_inputs` when the dependent item should not leave
  `BLOCKED` until the prerequisite PR is merged
- set `requires_materialized_refs` when the dependent item's exporter resolves
  baseline evidence by repo path, not only by DB metadata

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

## 3. quality_gate.md

### Purpose

Record the numerical or model-quality precheck required before remote PPA spend
for proposals that may affect output semantics.

Examples:
- quantization changes
- activation-function changes
- softmax/layernorm lowering changes
- mapper changes that can alter output tensors

### Required sections

```md
# Quality Gate

## Proposal
- `proposal_id`
- short title

## Why This Gate Is Required
- what output semantics may change
- why PPA-only evaluation would be insufficient

## Reference
- accepted baseline path
- software reference path or tool

## Checks
- required comparison checks
- exact thresholds

## Local Commands
- commands run

## Result
- pass | fail | pending
- short explanation
```

## 4. analysis_report.md

### Purpose

Summarize evaluated evidence for a promotion decision.

Timing:
- update this artifact after the evaluation PR that contains the evidence is
  merged
- treat the merged PR and its committed artifacts as the canonical evidence
  boundary
- only write pre-merge draft analysis when a human explicitly asks for it

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
- whether the baseline was:
  - historical context only
  - refreshed reference point
  - direct paired-comparison baseline

## Result
- win / loss / mixed
- confidence level
- estimated mapper optimization room
- whether the architecture conclusion is robust to plausible schedule changes
- whether any non-win/lose result matched expectation

## Failures and Caveats
- flow failures
- validation anomalies
- mapper limitations

## Recommendation
- reject / iterate / promote
- short reason
- follow-on mapper item or proposal when iteration is caused by mapper limits
```

`analysis_report.md` should make it obvious whether a result is:
- an architecture win or loss that is robust under the current evidence
- a mapper-confounded outcome that should remain in `iterate`

When mapper limitations are material, include:
- the likely unused optimization room
- why the benchmark shape does or does not stress the architecture fairly
- what bounded follow-on mapper work would reduce the ambiguity

## 5. promotion_decision.json

### Purpose

Provide a small machine-readable decision record after analysis.

Timing:
- write or update this artifact after `analysis_report.md`
- do not treat a still-open evaluation PR as final evidence by default
- this artifact should reflect the merged evidence set and the current accepted
  next step

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

When `decision` is `iterate`, `next_action` should identify the bounded next
step. For mapper-confounded results, prefer an intake item id or mapper
proposal path rather than a vague free-form note.

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
