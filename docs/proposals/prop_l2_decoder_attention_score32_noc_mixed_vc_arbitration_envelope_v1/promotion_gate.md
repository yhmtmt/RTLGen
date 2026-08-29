# Promotion Gate

Promote a shared-mesh overlap point only if it conserves every exact flit,
requires no more than one queued flit per source VC, and records zero endpoint
injection stalls. Otherwise retain the result as a queue-depth diagnostic and require a
backpressure-coupled endpoint replay with measured SRAM-residency and local
reducer readiness events.

The local endpoint arbiter must be embodied and RTL/performance equivalent
before its area, energy, or timing replaces a measured dual-network component.
