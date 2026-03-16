# Developer Agent Orchestration

## Purpose

Define the practical notebook-side procedure for running the developer-agent
loop without expanding the control-plane scheduler.

This document answers:
- who creates which artifact
- when approvals are requested
- how the loop advances from idea to remote evaluation to promotion

It complements:
- `docs/developer_agent_loop.md`
- `docs/developer_agent_first_read.md`
- `docs/developer_agent_artifacts.md`
- `control_plane/operator_runbook.md`

## Initial Operating Rule

Keep notebook-side creative orchestration file-based and branch-based.

Do not add new DB task types for:
- proposals
- implementation summaries
- analysis reports
- promotion decisions

Use the current control plane only for:
- deterministic remote evaluation execution
- artifact return
- submission preparation

## Working Area

Use one notebook-side working branch per candidate direction.

Recommended branch pattern:
```text
dev/<proposal_id>
```

Examples:
```text
dev/prop_l1_prefix_variant_v1
dev/prop_l2_softmax_tile_fusion_v1
```

That branch should contain:
- implementation changes
- notebook-side decision artifacts
- any local docs needed for the checkpoint discussion

## Standard Procedure

### Step 1. Create Proposal Branch

Notebook developer agent:
1. reads the bounded startup context in `docs/developer_agent_first_read.md`
2. chooses or reuses `proposal_id`
3. creates or updates a working branch `dev/<proposal_id>`
4. writes:
   - `design_brief.md`
   - `proposal.json`

Notebook developer agent should determine `proposal_id` only after:
- checking current open proposal directories,
- reading topic-relevant baselines,
- incorporating the current user direction.

Recommended `proposal_id` form:
```text
prop_<layer>_<topic>_<change>_vN
```

Examples:
```text
prop_l1_prefix_variant_v1
prop_l2_softmax_tile_fusion_v1
```

This avoids deriving a task identity from stale session residue.
Recommended artifact location:
```text
docs/developer_loop/<proposal_id>/
```

Bootstrap from:
```text
docs/developer_loop/_template/
```

Or use:
```sh
/workspaces/RTLGen/scripts/bootstrap_developer_loop.sh <proposal_id> [layer] [kind]
```

Initial file set:
```text
docs/developer_loop/<proposal_id>/
  design_brief.md
  proposal.json
```

### Step 2. Direction Gate

Human checkpoint.

Approval input:
- `design_brief.md`
- `proposal.json`

Approval result should be recorded explicitly.

Recommended mechanism:
- add a short note to `design_brief.md`
- or add a small `direction_gate.md`

Minimum record:
```md
## Direction Gate
- status: approved | rejected
- approved_by: <operator>
- approved_utc: <timestamp>
- note: <short reason>
```

### Step 3. Implementation

If approved, the developer agent:
1. implements the candidate
2. runs notebook-local validation
3. writes `implementation_summary.md`

Updated file set:
```text
docs/developer_loop/<proposal_id>/
  design_brief.md
  proposal.json
  implementation_summary.md
```

Implementation summary must include:
- changed files
- local commands run
- known remaining risks
- requested remote evaluation

### Step 4. Evaluation Gate

Human checkpoint.

Approval input:
- `implementation_summary.md`
- local smoke/regression results

Approval result should be recorded explicitly.

Recommended file:
```text
docs/developer_loop/<proposal_id>/evaluation_gate.md
```

Minimum content:
```md
## Evaluation Gate
- status: approved | rejected
- approved_by: <operator>
- approved_utc: <timestamp>
- allowed_evaluations:
  - <task summary>
- note: <short reason>
```

### Step 5. Queue Generation

If approved, notebook developer agent:
1. creates deterministic DB-native work items through the control plane
2. records the created item ids in the proposal directory

Recommended file:
```text
docs/developer_loop/<proposal_id>/evaluation_requests.json
```

Recommended fields:
```json
{
  "proposal_id": "string",
  "source_commit": "git sha",
  "requested_items": [
    {
      "item_id": "string",
      "task_type": "l1_sweep | l2_campaign",
      "objective": "string",
      "candidate_id": "string"
    }
  ]
}
```

### Step 6. Remote Evaluation

This step is fully handled by the existing control plane.

Evaluator daemon:
- detects the queued items
- executes them
- syncs allowlisted evidence

Notebook side:
- use `daily_ops.sh`
- use `operator_status.sh`
- wait until items reach:
  - `AWAITING_REVIEW`
  - or terminal `FAILED`

### Step 7. Result Analysis

After enough evidence is available, the notebook analysis agent:
1. reads the completed evidence
2. writes:
   - `analysis_report.md`
   - `promotion_decision.json`

Updated file set:
```text
docs/developer_loop/<proposal_id>/
  design_brief.md
  proposal.json
  implementation_summary.md
  evaluation_gate.md
  evaluation_requests.json
  analysis_report.md
  promotion_decision.json
```

### Step 8. Promotion Gate

Human checkpoint.

Approval input:
- `analysis_report.md`
- `promotion_decision.json`
- linked run evidence and candidate diffs

Recommended file:
```text
docs/developer_loop/<proposal_id>/promotion_gate.md
```

Minimum content:
```md
## Promotion Gate
- status: approved | rejected
- approved_by: <operator>
- approved_utc: <timestamp>
- action: merge | rerun | iterate
- note: <short reason>
```

### Step 9. Promotion / Merge

If approved, notebook developer agent:
1. submits or refreshes the PR
2. links the PR number in the proposal directory
3. merges after review

Recommended final file:
```text
docs/developer_loop/<proposal_id>/promotion_result.json
```

Suggested fields:
```json
{
  "proposal_id": "string",
  "decision": "promoted",
  "pr_number": 0,
  "merge_commit": "git sha",
  "merged_utc": "ISO-8601 timestamp"
}
```

## Rejected Or Iterated Candidates

Do not delete failed or rejected proposal directories immediately.

Instead:
- keep the proposal directory on the notebook branch while the direction is active
- if the candidate is conclusively dead, either:
  - drop the branch before merge, or
  - preserve only the final `proposal.json` and `analysis_report.md` if you want audit history

Initial policy recommendation:
- keep iterative work notebook-local until a candidate is promotion-worthy
- do not merge every failed idea into `master`

## Candidate Identity Rule

Use:
- one `proposal_id` per direction
- one `candidate_id` per implemented revision

Example:
- `proposal_id = prop_l2_softmax_tile_fusion_v1`
- `candidate_id = cand_l2_softmax_tile_fusion_v1_r2`

That lets one proposal survive multiple remote evaluation rounds without losing identity.

## Approval Recording Rule

Do not keep approvals only in chat history.

Each approval gate must leave a repo-visible artifact on the notebook branch:
- `direction_gate.md`
- `evaluation_gate.md`
- `promotion_gate.md`

That keeps the notebook-side autonomous loop auditable without inventing new infrastructure first.

## Why This Is The Right Initial Form

This procedure is intentionally conservative:
- no new DB schema
- no new service roles
- no extra evaluator complexity

But it still gives:
- bounded candidate identity
- explicit approval points
- file-based traceability
- clean handoff into the already-working control-plane evaluator path
