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

## Merge Policy

For now:

- agent review may draft findings
- human approval still owns final merge

This remains true even if the review package is complete.
