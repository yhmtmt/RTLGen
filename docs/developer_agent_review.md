# Developer Agent Review

## Purpose

Define the minimum review context required for a fresh notebook-side session to
review a developer-agent PR correctly.

This is not a replacement for proposal history.
It is the serialization of that history into repo-backed review inputs.

## Reviewer First Read

For a PR linked to a developer-loop proposal, read in this order:

1. `docs/developer_agent_first_read.md`
2. `docs/developer_agent_review.md`
3. proposal workspace:
   - `design_brief.md`
   - `proposal.json`
   - `implementation_summary.md`
   - `quality_gate.md` when present
   - `evaluation_gate.md`
4. review payload:
   - `control_plane/shadow_exports/review/<item_id>/evaluated.json`
   - `control_plane/shadow_exports/review/<item_id>/review_package.json`
   - PR body
5. baseline evidence directly referenced by the proposal

Do not start from old chat context.
Start from these files.

## Required Proposal Linkage

Every developer-loop evaluation item should carry:

- `proposal_id`
- `proposal_path`

These must be visible in:

- queued payload
- `evaluated.json`
- `review_package.json`
- PR body

If proposal linkage is missing, the review is incomplete and should be treated
as lower-confidence.

## Review Questions

The reviewer must answer:

1. Did the run evaluate the intended proposal, not just a technically valid task?
2. Did it use the intended baseline and objective framing?
3. Did it satisfy the proposal’s required gates and evidence rules?
4. Does the result support the proposal’s stated hypothesis?
5. Are the claimed improvements meaningful against the referenced baseline?
6. Does the PR contain the exact evidence required for reproducibility?

## Focused Comparison Rule

Review the result against the proposal's declared direct comparison set first.

Do not let a broader architecture sweep override the primary proposal question
when the proposal was intentionally scoped more narrowly.

Examples:
- if the proposal is about fusion on `nm1`, the first review question is the
  fused vs non-fused delta on `nm1`, not whether `nm1` still beats `nm2`
- if the proposal is about a mapper change on `nm2`, the first review question
  is the old-mapper vs new-mapper delta on `nm2`, not whether `nm2` becomes the
  global rank-1 point

When a broader sweep is present, distinguish explicitly between:
- proposal outcome: did the focused hypothesis succeed?
- campaign ranking: which point wins under the broader objective?

If the direct comparison set is missing or mixed together with a much broader
comparison set, treat the review as lower-clarity and call that out.

## Mapper Headroom Rule

The reviewer should not treat every losing or flat result as an architecture
loss.

Before concluding `reject` or writing a negative finding, explicitly assess:
- whether the run used one narrow mapper heuristic or a bounded set of schedule
  alternatives
- whether the losing architecture exposed unused parallelism, overlap, tiling,
  or memory-placement choices that the current mapper did not explore
- whether the benchmark model family is large enough and shaped appropriately to
  exercise the architecture's intended advantage
- whether the observed gap is better explained by mapper overhead, control
  synchronization, or benchmark mismatch than by the hardware itself

Prefer `iterate` over a stronger negative conclusion when:
- the architecture result is technically valid but still mapper-confounded
- the benchmark likely leaves meaningful optimization room unused
- the proposal question has shifted from "is the hardware legal?" to "did the
  mapper expose the hardware fairly?"

Prefer `reject` only when:
- the architecture loses for reasons unlikely to be rescued by reasonable
  mapper improvements
- the relevant mapping alternatives were already explored enough to make the
  conclusion robust
- the benchmark family is appropriate for the proposed architectural advantage

When mapper headroom is part of the conclusion, the review should say so
explicitly and point to the follow-on mapper intake item or proposal when one
exists.

## Merge Policy

For now:

- agent review may draft findings
- human approval still owns final merge

This remains true even if the review package is complete.
