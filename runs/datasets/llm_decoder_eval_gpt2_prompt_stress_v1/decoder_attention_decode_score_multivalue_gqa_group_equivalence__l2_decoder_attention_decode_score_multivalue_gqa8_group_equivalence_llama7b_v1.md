# Llama7B GQA8 Shared-K/V Arithmetic Equivalence

- decision: `llama7b_gqa8_shared_kv_equivalence_pass`
- equivalence pass: `True`
- real single-cluster arithmetic pass: `True`
- wrapper sharing/order protocol pass: `True`
- expected group result hash: `e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069`
- observed group result hash: `e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069`

## Compositional Proof

The real generated single-cluster RTL is simulated independently for each of eight distinct query heads against the perf/reference math, while every run uses identical key and value tensors.

The focused wrapper protocol test verifies atomic shared-key broadcast, one shared external value replay, and deterministic head-major then slice-major result order.

Because the wrapper only broadcasts shared keys and shared value responses to arithmetic-equivalent children and serializes their unchanged results in the tested order, the two checks compose to the GQA8 claim.

**Scope:** This is a compositional proof; it does not claim that a flat eight-cluster RTL simulation was run.
