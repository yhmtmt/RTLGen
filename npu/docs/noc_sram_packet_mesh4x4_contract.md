# SRAM Packet Mesh Composition Contract

`noc_sram_packet_mesh4x4` is the exact functional boundary between sixteen
descriptor-driven SRAM endpoints and the 4x4 segmented NoC.

## Included RTL

- Sixteen `noc_sram_packet_endpoint` instances.
- Sixteen five-port deterministic-XY routers.
- Four virtual channels and four entries per input/VC FIFO.
- All 24 bidirectional neighbor connections.
- Full 256-bit payload, source, destination, VC, tag, fragment, and `last`
  transport.
- Direct receive SRAM writes, packet completion, and per-endpoint protocol
  errors.
- Registered-occupancy FIFO credits; no router-to-router combinational ready
  path exists.

## External Contracts

- The command scheduler must install receive descriptors before releasing the
  matching transmit descriptors.
- Source SRAM returns one in-order response for each accepted read request.
- Destination SRAM accepts each write only on ready/valid handshake.
- SRAM arrays and bitcells are external; their address, data, and flow-control
  boundaries are explicit rather than modeled as zero-cost storage.
- HBM/DRAM and its controller remain outside the chip-level RTL scope.

## Backpressure Semantics

FIFO input readiness depends only on registered occupancy. A non-full FIFO can
accept and pop in the same cycle at one flit/cycle. A full FIFO that resumes
after downstream blockage first releases one entry, then advertises credit on
the following cycle. The performance model uses the same rule; it no longer
solves a combinational ready fixpoint across the mesh.

## Current Evidence

The end-to-end test concurrently transfers an eight-flit packet from endpoint
0 to 15 and a three-flit packet from endpoint 3 to 12. It checks exact source
SRAM data, multihop delivery, destination-specific write addresses, completion
metadata, backpressure, and zero protocol errors. Structural synthesis checks
the complete sixteen-endpoint/sixteen-router hierarchy.

This is functional composition evidence. Aggregate physical placement and
workload-matched switching activity remain separate gates.

The workload replay extension uses compact runtime descriptor memories to
exercise the same hierarchy without embedding a packet list in generated RTL.
Its paired scheduler installs each receive context before transmit release,
serves one-cycle in-order source SRAM responses, verifies every destination
write and completion, and compares drain/congestion counters with
`npu.sim.perf.noc_sram_packet_mesh`. A local eight-source contention gate proves
exact counters with full RX-context occupancy; the workload-complete Llama7B
replay remains a bounded remote evaluation gate.
