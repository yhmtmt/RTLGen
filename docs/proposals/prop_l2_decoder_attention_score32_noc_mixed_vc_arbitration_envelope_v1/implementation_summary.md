# Implementation Summary

- Added explicit FIFO and per-VC round-robin endpoint injection policies to
  the cycle-level registered-credit mesh model.
- Added counter-only mesh replay for repeated full-workload sweeps without
  retaining RTL replay objects.
- Added a shared-router envelope over all five exact transport phases.
- Added source queue-depth and stall-free replay gates so optimistic overlap
  rows cannot become architecture recommendations.
- Embodied the two-source VC0/VC1 endpoint arbiter in RTL and proved its
  ready/valid behavior cycle-equivalent to both a standalone model and the
  shared-mesh injection trace.
- Extracted the exact sixteen-node SRAM packet endpoint array from the legacy
  endpoint-plus-mesh wrapper without changing its descriptor, SRAM, completion,
  or protocol-error contracts.
- Added optional external transport mode to both exact producers. Structural
  synthesis proves that external mode contains zero private meshes, and RTL
  replay proves that routing the exposed boundary through a separately
  instantiated mesh preserves each producer's exact behavior.
- Retained internal transport as the default compatibility mode, with exactly
  one endpoint array and one private mesh for VC0 and exactly one private mesh
  for VC1.
- Added a shared dual-producer transport containing sixteen held-grant
  endpoint arbiters, exactly one segmented mesh, a VC0/VC1 ejection demux, and
  fail-closed sticky errors for invalid injection or ejection VC identities.
- Forwarded the external transport boundary through the complete VC0
  admission service and composed that service with the complete VC1 reducer,
  packet adapters, root storage, decoder, and final tree on the shared fabric.
- Exposed the shared router accounting vectors to the exact reducer accounting
  path and made the VC1 TX-only ejection readiness deterministic.
