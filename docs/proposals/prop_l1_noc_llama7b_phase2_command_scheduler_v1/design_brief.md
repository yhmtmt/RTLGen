# Design Brief

The checked Llama7B Phase-2 schedule contains eight waves, sixteen clusters,
68 shared-payload packets for each remote tile, and 33 reduction packets for
each non-root cluster. Shared-SRAM home wave 4 is local and emits no shared
traffic. Nine release epochs, wave/class/cluster/packet counters, and simple
route, tag, packet-ID, and base-address formulas therefore reproduce all
11,576 102-bit commands exactly.

The generator holds its output under backpressure and advances only when the
paired scheduler accepts a command. It replaces a 1,180,752-bit (147,594-byte)
static command image plus an unspecified refill producer. This is a
workload-specific hardware point: changing the topology, packetization,
precision, or schedule requires regeneration and a new exhaustive equivalence
proof.
