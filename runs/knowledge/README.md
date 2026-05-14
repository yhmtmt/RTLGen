# Run Knowledge

This directory stores small, reviewable knowledge artifacts that prevent the
control loop from repeating already-known expensive failures.

`infeasible_designs.json` is an exact-match skip registry for synthesis points
that previously consumed the bounded evaluator budget without producing useful
PPA. Entries should be narrow enough not to block diagnostic variants or
structurally changed RTL.
