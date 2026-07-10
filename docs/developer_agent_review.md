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

`proposal_path` should identify the exact proposal file in repo-relative form,
normally `docs/proposals/<proposal_id>/proposal.json`. Directory paths are only
acceptable when the control-plane tooling canonicalizes them to that exact
file; broad ancestors such as `docs/proposals/` are invalid.

These must be visible in:

- queued payload
- `evaluated.json`
- `review_package.json`
- PR body

The artifact PR must also include the proposal workspace files referenced by
`reviewer_first_read`, especially `proposal.json` and
`evaluation_requests.json`. If proposal linkage is missing, does not resolve, or
points to files absent from the PR branch, the evidence package is incomplete;
fix packaging before reviewing or merging the PR.

## Review Questions

The reviewer must answer:

1. Did the run evaluate the intended proposal, not just a technically valid task?
2. Did it use the intended evaluation mode, baseline, and objective framing?
3. Did it satisfy the proposal’s required gates and evidence rules?
4. Does the result support the proposal’s stated hypothesis?
5. Are the claimed improvements meaningful against the referenced baseline?
6. Does the PR contain the exact evidence required for reproducibility?
7. If the item depends on prior developer-loop evidence, were those
   prerequisites merged and materialized before this PR was exported?

## Focused Comparison Rule

Review the result against the proposal's declared direct comparison set first.

For `measurement_only` or `baseline_refresh` items:
- do not force a win/lose proposal judgment
- check whether the item recorded the intended metrics or refreshed the intended
  reference point
- check whether the observed shift matched the declared expectation and reason

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
- measurement result: what metric reference point was recorded without proposal
  judgment?

If the direct comparison set is missing or mixed together with a much broader
comparison set, treat the review as lower-clarity and call that out.

## Revision and Retraction Rule

If merged evidence is later found to have used the wrong configuration, missing
connectivity, wrong baseline, or another invalidating setup error, do not erase
the historical PR or artifact. Mark it out of the active decision path and
replace it with an explicit revision item.

A corrective evaluation against a finalized proposal must declare a revision in
`evaluation_requests.json`:

- `revision.reason`: short invalidation reason, for example
  `wrong_configuration`
- `revision.invalidates_item_ids`: prior requested item IDs that should no
  longer contribute to active proposal decisions
- optional `revision.invalidates`: structured references such as PR numbers,
  run keys, or artifact paths

When the corrective PR is finalized, the finalizer marks invalidated requested
items as `retracted`, records the replacement item, and updates
`promotion_decision.json` / `promotion_result.json` with revision metadata. The
old artifacts remain audit evidence, but dashboard rankings, proposal summaries,
and follow-on decisions should use the replacement evidence.

Reviewers should reject or block a corrective PR that claims to revise a
finalized proposal but does not state what it invalidates and why.

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

## Boundary Metric Rule

Some physical exploration jobs are intended to find the point where a design
stops being feasible. For those jobs, a `flow_failed` or timing-failed
`metrics.csv` row can be valid evidence rather than a bad submission.

When preparing or reviewing a boundary job:
- the objective must say that timing/flow failures are accepted as boundary
  evidence
- the L1 acceptance rule must allow non-ok metrics rows with a valid `status`
  column
- the report must distinguish a useful boundary failure from an infrastructure,
  checkout, or validation failure

Do not use relaxed boundary acceptance for ordinary winner-selection sweeps.
Those should continue to require at least one `status=ok` row for each expected
metrics file.

## Semantic Equivalence And Proxy Rule

Do not treat generator syntax checks, a folded result hash, or agreement on
independent single operations as proof of composed datapath equivalence.

For a producer-consumer datapath claim, the evidence must cover:

- the producer's complete architectural output, not an XOR/fold proxy
- every stateful intermediate consumed by the next stage
- the final architectural output vector
- sequential visibility: a consumer cannot observe data before producer
  completion
- ready/valid ordering, backpressure, loss, and duplication behavior
- the same precision profile and rounding rules on both perf and RTL sides

A hash is acceptable as secondary compression after exact stage traces have
established the contract. Hash-only evidence is not sufficient for first
promotion of a composed path. PPA stimulus generation must also be separated
from the claimed datapath cost, or its hardware overhead must be identified
explicitly; expensive pseudo-random or modulo logic is not a valid substitute
for ordinary input registers.

## Merge Policy

Evaluation PR merge rule:

- merge the PR when it is valid, self-contained evidence for the proposal's
  direct comparison
- do not hold merge until after notebook-side analysis artifacts are updated
- a flat or negative result can still be merge-worthy if the evidence is
  correct

Post-merge rule:

- once the evidence PR is merged, update the proposal workspace with:
  - `analysis_report.md`
  - `promotion_decision.json`
- use those artifacts to record whether the next step is `promote`, `iterate`,
  or `reject`

For now:

- agent review may draft findings
- human approval still owns final merge

This remains true even if the review package is complete.
