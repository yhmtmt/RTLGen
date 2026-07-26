# Score32 Exact Partial Reduction Contract

This phase changes the reduction boundary from locally normalized values to exact
streamed partial state.

## Contract

- Local decode-score multivalue reducers may still expose the existing normalized
  interface by default.
- The new `exact_partial` mode instead emits, per value slice beat:
  - `command_id`
  - `head_id`
  - signed `S32` global max
  - unsigned `U33` exponent sum
  - slice index and `last`
  - `8 x signed S41` weighted numerators (`328` payload bits)
- Pairwise merge must operate only on that exact partial state, with the same
  LUT correction, symmetric rounding, and saturation semantics as the Python
  reference.
- Hardware equivalence hash remains disabled for these PPA-facing variants.

## Capacity Delta

The current proxy used in the physical-feasibility study assumed a
`141`-cycle cross-cluster reduction with `8320 B/cluster` of payload.

The exact state is materially larger:

- per head: `32 + 33 + 16 * 8 * 41 = 5313 bits`
- per 32-head cluster: `5313 * 32 / 8 = 21252 B`

That is the state this exact-partial boundary preserves. It closes the merge
semantics gap that appears when already-normalized local outputs are merged
later.

## Non-Goals For This Phase

- No claim that final normalization or divider PPA is closed here.
- No claim that the full 16-cluster tree wrapper, NoC transport schedule, or
  SRAM placement is physically closed here.
- The next boundary is the streamed finalizer/tree composition on top of this
  exact partial contract.
