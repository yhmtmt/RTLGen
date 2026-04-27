# Artifact-sync proposal packaging probe

- item_id: `item_cp_artifact_sync_proposal_packaging_probe_v1`
- layer: `cross`
- kind: `architecture`
- status: `seed`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-27T23:20:00Z`
- updated_utc: `2026-04-27T23:20:00Z`
- proposal_id:
- proposal_path:
- triggered_by_proposal: `prop_l2_llm_attention_tail_v1`
- triggering_evidence: `PR #219`, `PR #218`

## Problem
- PR #219 fixed artifact submission packaging so proposal workspace files are
  included from the resolved `developer_loop.proposal_path`.
- The original PR #218 failure showed that a future developer-loop item can
  still become hard to review if proposal linkage is missing, broad, stale, or
  not packaged into the artifact PR.
- The current tests cover the implementation path, but there is not yet a
  small operator-visible probe that proves the full artifact-sync behavior from
  queued metadata through generated review package.

## Candidate Idea
- add a bounded control-plane probe that exercises proposal linkage and
  submission packaging without running a costly physical evaluation
- use a synthetic proposal workspace and a completed lightweight work item to
  drive the same artifact-sync packaging path used by real L1/L2 evidence PRs
- assert both the positive and negative resolver behavior:
  - exact `docs/proposals/<proposal_id>/proposal.json` linkage packages the
    proposal scaffold
  - broad `docs/proposals/` linkage is rejected before PR export

## Why It Might Matter
- prevents recurrence of the missing proposal artifact failure seen while
  preparing PR #218
- verifies that the stricter resolver added by PR #219 remains wired into the
  real submission path, not only into a narrow helper test
- gives future developer-agent sessions a concrete acceptance test before
  queuing more proposal-backed evaluations

## Required Work
- control-plane test or dry-run command that creates a temporary proposal
  scaffold with:
  - `proposal.json`
  - `evaluation_requests.json`
- positive packaging check:
  - queued payload includes `developer_loop.proposal_id`
  - queued payload includes `developer_loop.proposal_path` pointing to the exact
    `proposal.json`
  - prepared submission branch includes the proposal scaffold files referenced
    by `reviewer_first_read`
- negative packaging check:
  - broad parent path such as `docs/proposals/` is rejected as invalid proposal
    linkage
  - stale or missing proposal paths are reported as proposal-linkage failures
    before artifact PR creation

## Evaluation Sketch
- local:
  - run the probe in a temporary repo/control-plane database fixture
  - verify the generated review package and prepared submission tree contain
    the expected proposal files
  - verify invalid broad paths do not copy unrelated proposal directories
- remote:
  - optional one-shot operator dry run after the local probe lands
  - dashboard should show no `artifact_sync` eligibility error for the positive
    case and a clear proposal-linkage error for the negative case

## Inputs / Sources
- `control_plane/control_plane/services/submission_bridge.py`
- `control_plane/control_plane/services/docs_paths.py`
- `control_plane/control_plane/services/operator_submission.py`
- `control_plane/control_plane/tests/test_submission_bridge.py`
- `docs/workflows/developer_loop.md`
- `docs/developer_agent_review.md`
- `https://github.com/yhmtmt/RTLGen/pull/219`
- `https://github.com/yhmtmt/RTLGen/pull/218`

## Open Questions
- whether the probe should stay as a pytest integration test only or also gain
  an operator CLI wrapper
- whether the negative broad-path case should be exposed in dashboard status as
  a distinct resolver reason or kept under the existing proposal-linkage error

## Promotion Rule
- promote when the probe can fail before PR export for bad proposal linkage and
  can prove that valid proposal linkage packages the exact proposal scaffold
  into the artifact submission branch
