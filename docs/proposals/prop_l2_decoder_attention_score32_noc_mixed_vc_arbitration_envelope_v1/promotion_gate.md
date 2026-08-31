# Promotion Gate

Promote a shared-mesh overlap point only if it conserves every exact flit,
requires no more than one queued flit per source VC, and records zero endpoint
injection stalls. Otherwise retain the result as a queue-depth diagnostic and require a
backpressure-coupled endpoint replay with measured SRAM-residency and local
reducer readiness events.

Both producer boundaries must elaborate without private meshes and preserve
their exact standalone workload when connected to an external mesh. The
cycle-equivalent local endpoint arbiters must then be composed at all sixteen
injection ports with one shared mesh and a VC-aware ejection demux. Promotion
requires a simultaneous backpressure-coupled RTL replay that conserves every
VC0 and VC1 flit and completion, reports no protocol error, and matches the
cycle model's arbitration decisions. The resulting shared top must be
physically measured before its area, energy, or timing replaces a measured
dual-network component.

The bounded simultaneous replay remains an integration gate only. The actual
composed top has now also passed the full 70,948-flit replay, so exact workload
integrity and simultaneous backpressure behavior are satisfied. The full
sixteen-endpoint arbitration trace also matches independent cycle models
decision-by-decision, satisfying functional policy promotion. The point still
cannot establish or replace the Llama7B frontier until its composed hierarchy
has measured timing, area, and power evidence.
