# Design Brief

The prior exact activity job validates five isolated phases but cannot measure
simultaneous VC0/VC1 arbitration. The integrated GQA8 artifact records final
root bounds and counts, not cycle-aligned shared-SRAM residency or local
reducer release events, so one authoritative mixed release schedule is not
available.

This job keeps every exact phase flit and replays them on one registered-credit
deterministic-XY mesh. Endpoint injection is compared with a per-VC
round-robin arbiter and an arrival-ordered FIFO. The first VC1 group starts at
0, 25, 50, 75, or 100 percent of the measured VC0 service duration; later VC1
groups retain the sequential two-slot adapter lifecycle.

The isolated source traces continue producing while their shared queue is
blocked. Consequently the maximum queued flits are a required-buffer bound.
Only rows with at most one queued flit per VC are directly compatible with the
current one-register ready/valid source boundary.

The two-source arbiter is now embodied and cycle-equivalent. The VC0 attention
context engine and VC1 exact reducer transport also expose their complete
sixteen-endpoint ready/valid flit boundaries. Each producer has an
`INTERNAL_MESH=0` elaboration with no private mesh, while the default private
mesh elaboration preserves the existing exact workload behavior. The SRAM
packet endpoints remain embodied on the VC0 side; the exact packet bridges,
encoders, adapters, and shared-root composition remain embodied on the VC1
side.

The composition above these boundaries is now embodied as one top containing
the complete VC0 admission/service hierarchy, the complete VC1 exact
stats-once reducer hierarchy, sixteen held-grant VC arbiters, one shared mesh,
and a VC-aware ejection demux. Both producer-private meshes are disabled, and
the shared mesh's accounting vectors feed the reducer's existing transport
counter contract.

The remaining transport evidence is dynamic and physical rather than
structural: simultaneous backpressure-coupled execution must first pass a
bounded overlap proof, then the full 60,928-flit VC0 plus 10,020-flit VC1
workload. A registered activity boundary must physically measure the composed
top before its cost or overlap replaces the measured dual-network baseline.
