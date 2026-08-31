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
- Passed a bounded simultaneous composed-top replay: four VC0 contexts moved
  64 payload-checked SRAM words while one exact VC1 group moved 315 packets
  and 2,505 flits into 128 value-checked root rows. The replay observed both
  producers accepting flits at overlapping endpoints, active arbitration,
  nonzero mesh contention/stalls, and zero protocol errors.
- Passed the promotion-scale simultaneous composed-top replay on the actual
  shared-mesh RTL: all 112 VC0 contexts moved 7,616 packets and 60,928 flits,
  while four sequential VC1 groups moved 1,260 packets and 10,020 flits into
  512 value-checked root rows. The replay checked VC0 SRAM payloads, writes,
  completions, VC1 metadata, values, descriptors, completions, and held output
  behavior under stalls. It observed real overlapping endpoint arbitration and
  nonzero contention with zero protocol errors.
- The promotion-scale gate is reproducible with
  `RTLGEN_RUN_SLOW_SHARED_MESH_FULL_REPLAY=1 python -m pytest -q
  tests/test_attention_score32_exact_dual_producer_shared_mesh4x4_full.py`;
  the verified run completed in 353.16 seconds.
- Extended that promotion-scale gate with a compact per-cycle trace of all
  sixteen endpoint arbiters. Sixteen independent
  `EndpointVcInjectionArbiter` models now compare both producer-ready signals,
  output validity, and selected VC decision-by-decision for the full replay;
  the trace-equivalent run passed in 274.24 seconds.
- Proved the composed hierarchy contains one VC0 service, one VC1 reducer, one
  shared transport, exactly one mesh, and sixteen endpoint arbiters, with no
  producer-private mesh remaining.
