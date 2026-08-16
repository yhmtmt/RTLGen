# Design Brief

The canonical Phase-2 packet list is converted to concrete descriptors with
8-bit tags. Sixteen destination queues install receive contexts in static
release order; sixteen source queues release transmit descriptors only after
the matching receive handshake. Source SRAM provides one in-order response per
cycle and destination SRAM accepts one write per cycle.

The same descriptor list runs through:

1. `npu.sim.perf.noc_sram_packet_mesh`, including finite queues and registered mesh credits.
2. `noc_sram_packet_mesh4x4`, including all sixteen endpoints and routers.

Packets, flits, drain cycles, aggregate contention, aggregate input stalls, and
maximum occupancy must agree exactly. Every destination write checks address
and payload identity, and every completion checks source, VC, and tag.

SRAM bitcells, a synthesized command scheduler, HBM/DRAM, and activity-derived
power remain outside this functional equivalence boundary.
