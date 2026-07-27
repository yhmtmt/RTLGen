# Score32 Exact Partial Tree Contract

This phase closes the cross-cluster merge semantics with a streamed radix-2
tree built from the exact-partial pair primitive.

## Contract

- Each leaf is an independent ready/valid exact-partial stream.
- Each beat carries `command_id`, `head_id`, signed `S32` global max, unsigned
  `U33` exponent sum, slice index, `last`, and `8 x signed S41` numerators
  (`328` payload bits).
- The tree preserves left-to-right level-wise pairing. There is no merge path
  through locally normalized values.
- Each pair node buffers only its current left/right beat. There is no
  monolithic 16-cluster x full-head exact-state register in this phase.
- Sticky protocol errors and completed-count monitors are exposed per node and
  per stage.

## Capacity And Traffic

- Theoretical full-Llama `32`-head exact preserved state remains
  `21252 B/cluster`.
- The streamed leaf link repeats metadata on every slice beat, so one cluster
  emits `26816 B` for `32` heads across the direct exact-partial link.
- A 16-cluster spatial tree therefore carries `429056 B` of leaf traffic for a
  full `32`-head reduction wave before the finalizer.

## Probe Evidence

- Quick smoke probes may use smaller head counts for `c2`/`c4` runtime.
- The real `c16` regression now runs the full `32`-head workload:
  `512` accepted beats per leaf, `8192` total leaf beats, and `512` root
  outputs under deterministic skew and root backpressure.
- Probe reports must label measured workload counts/cycles separately from the
  theoretical `32`-head capacity numbers above.

## Boundaries Still Open

- The links are still direct `328`-bit numerator payload streams with repeated
  metadata. No NoC or placement closure is claimed here.
- Final normalization/division is still the next boundary. The root currently
  emits merged exact partial state, not finalized values.
- Folded/time-multiplexed trees and radix-4 fan-in remain later area
  sensitivity work, not part of this verified phase-B implementation.
