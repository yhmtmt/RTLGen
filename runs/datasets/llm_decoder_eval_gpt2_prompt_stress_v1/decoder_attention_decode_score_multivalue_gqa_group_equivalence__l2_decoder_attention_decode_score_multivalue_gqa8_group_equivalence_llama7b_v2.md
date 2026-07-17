# Llama7B GQA8 Shared-K/V Arithmetic Equivalence

- decision: `llama7b_gqa8_shared_kv_equivalence_pass`
- equivalence pass: `True`
- real single-cluster arithmetic pass: `True`
- wrapper sharing/order protocol pass: `True`
- direct flat eight-cluster RTL pass: `True`
- expected group result hash: `e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069`
- observed group result hash: `e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069`

## Compositional Proof

The real generated single-cluster RTL is simulated independently for each of eight distinct query heads against the perf/reference math, while every run uses identical key and value tensors.

The focused wrapper protocol test verifies atomic shared-key broadcast, one shared external value replay, and deterministic head-major then slice-major result order.

Because the wrapper only broadcasts shared keys and shared value responses to arithmetic-equivalent children and serializes their unchanged results in the tested order, the two checks compose to the GQA8 claim.

**Scope:** The direct flat simulation is bounded to three KV blocks, but exercises all eight query heads, the full 128-element head dimension, all 16 value slices, shared K/V replay, intermediate score writes and reads, and all 128 ordered result beats.
