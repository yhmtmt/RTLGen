# Design Brief

The checked Llama7B Phase-2 schedule contains eight waves, sixteen clusters,
68 shared-payload packets for each remote tile, and 33 reduction packets for
each non-root cluster. Shared-SRAM home wave 4 is local and emits no shared
traffic. Nine release epochs, wave/class/cluster/packet counters, and simple
route, tag, and bounded endpoint-local base-address formulas therefore
reproduce all 11,576 102-bit commands exactly. Shared payloads use slots
0..67, reduction sources use slots 68..100, and root reduction receive
payloads use source-indexed slots 68..562. Each slot is 256 bytes, so the
largest endpoint-visible address extent is 144,128 bytes rather than the
global packet-ID-derived extent.

The generator holds its output under backpressure and advances only when the
paired scheduler accepts a command. It replaces a 1,180,752-bit (147,594-byte)
static command image plus an unspecified refill producer. This is a
workload-specific hardware point: changing the topology, packetization,
precision, or schedule requires regeneration and a new exhaustive equivalence
proof.
