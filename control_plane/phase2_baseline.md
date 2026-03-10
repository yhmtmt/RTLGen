# Phase 2 Baseline

Date: 2026-03-10

## Baseline Decision

The control-plane Phase 2 baseline is the DB-native operator workflow that can carry a completed work item through review packaging and draft PR submission.

## Stable Operator Command

```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main operate-submission \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --repo yhmtmt/RTLGen \
  --item-id <completed_item_id>
```

## Included Stages

1. publish review package
2. prepare submission branch and temporary worktree
3. push branch
4. open draft PR
5. query PR metadata
6. reconcile PR metadata back into `github_links`

## Baseline Guarantees

- DB-native Layer 1 and Layer 2 generation paths exist.
- Internal worker execution is proven on real repo workloads.
- Result consumers emit review artifacts for both layers.
- Review package publishing is available and idempotent.
- Submission branch preparation is available and reusable.
- Submission execution updates `github_links` and keeps the work item in `awaiting_review`.

## Intended Use

Use this baseline for real operator-driven internal submissions where:

- the work item is already completed,
- the result is review-worthy,
- and the operator wants a draft PR opened with the standard control-plane payloads.

## Not Yet Baseline

These remain outside the Phase 2 baseline:

- automatic eligibility policy / auto-submit gating
- unattended autonomous submission of all completed items
- merge automation
- PR comment / reviewer assignment automation
- production-hardening of GitHub/network failure retry policy

## Next Decisions

Only add policy controls after observing real operator usage and reviewer needs on top of this baseline.
