# Run Knowledge

This directory stores small, reviewable knowledge artifacts that prevent the
control loop from repeating already-known expensive failures.

`infeasible_designs.json` is an exact-match skip registry for synthesis points
that previously consumed the bounded evaluator budget without producing useful
PPA. Entries should be narrow enough not to block diagnostic variants or
structurally changed RTL.

Use `requires_repo_text` when the failure is tied to a specific old RTL
structure. This keeps the registry from suppressing a retry after the source has
changed in a way that may invalidate the failure.
