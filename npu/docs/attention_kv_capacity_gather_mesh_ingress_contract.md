# Exact K/V Capacity Gather Mesh-Ingress Contract

## Composition

`attention_kv_capacity_gather_mesh_ingress` composes the exact 32-layer gather
scheduler, sixteen source-local span packetizers, the endpoint-backed 4x4
deterministic-XY mesh, and payload-acceptance layer barriers.

One packetizer is attached to every physical injection endpoint. A descriptor
is routed by its explicit source endpoint, so the four HBM corners can expand
and inject different spans concurrently while owner-local resident traffic
uses the same endpoint interface. The verified four-corner case sustains four
simultaneous accepted packet commands and checks 16,384 commands across four
1 MiB spans.

## Packet Safety

For each packet, destination receive context is installed before the source
transmit descriptor is released. Arbitration is independent and round-robin
at each destination. The source endpoint, eight-flit count, packet tag/index,
and consume-versus-resident destination relation are checked before release.
Malformed commands fail closed.

Source descriptor addresses reserve bit 33 for HBM versus resident SRAM.
Destination descriptor addresses use bit 33 for resident-cache writes. A
canonical destination packs `layer[4:0]`, `tile[6:0]`, and the 20-bit tile byte
address. The packet endpoint increments only the low address range within a
256-byte packet, and ejection decodes this metadata into explicit resident
writes or per-cluster canonical ingress flits.

The payload test concurrently covers a corner-to-corner HBM transfer, HBM
refill to resident SRAM, owner-local resident transfer, and a multi-hop HBM
transfer. It verifies all 32 ejected flits, source response data, addresses,
canonical metadata, local routing, and downstream backpressure.

## Destination Descriptor Ordering

The partial tile splits each K/V plane into a resident prefix and an HBM
suffix, so packetizers at different source endpoints can be active for the
same destination. A destination ownership guard admits only one complete
gather descriptor per cluster at a time. It retains that lock after the
terminal packet command is submitted and releases it only when the matching
terminal packet completion is observed at the destination endpoint.

All packets within the active descriptor remain pipelined through the endpoint
queues and mesh. Descriptors targeting different clusters remain independent.
This preserves the scheduler's canonical descriptor order without reducing
the whole design to one global in-flight descriptor. Telemetry distinguishes
terminal packet submission from actual destination completion.

## Layer Barriers

Descriptor admission does not imply payload completion. The transient policy
therefore enforces two production constants:

- consume descriptors remain held until 69,632 resident refill flits
  (2,228,224 bytes) have been accepted for the active layer;
- the next layer remains held until 4,194,304 canonical consume flits
  (134,217,728 bytes) have been accepted.

The barrier fails closed on count overflow, layer skips, backwards layers,
consume descriptors for a future layer, or refill descriptors after consume
has begun. A parameterized RTL test exhaustively exercises the ordering with
small counts. Full quantities remain tied to the byte-conserving scheduler and
packet models; an attempted production refill replay exceeded the practical
Icarus CI budget, so it is not used as a routine regression.

## Remaining Boundary

Canonical ejection now reaches an ordered per-cluster ready/valid flit port.
The next RTL must derive K/V head and V block/fill targets and connect those
ports to the existing exact K ping-pong and V cluster-SRAM ingress modules.
V fill/drain overlap and characterized SRAM macros remain architecture
dimensions. The external HBM controller and PHY remain intentionally outside
the design boundary.
