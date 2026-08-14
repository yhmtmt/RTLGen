# NoC SRAM Packet Endpoint Contract

`noc_sram_packet_endpoint` closes the Phase 2 source-descriptor and packetizer
control abstraction between cluster SRAM and the 256-bit segmented mesh.

## TX Contract

- A descriptor names destination, VC, tag, source SRAM base address, and one to
  eight flits.
- Accepted descriptors are retained in a finite FIFO.
- The endpoint issues one in-order 256-bit SRAM read per fragment and retains
  metadata for every outstanding request.
- SRAM responses and metadata become a stable ready/valid flit stream.
- Payload storage remains in SRAM; the endpoint does not create a 2048-bit
  packet register.

## RX Contract

- Software or the command scheduler installs a finite receive context keyed by
  `(source, VC, tag)` before packet arrival.
- Each valid fragment is written directly to `base + fragment * 32` bytes.
- Contexts accept interleaved packets with different keys and enforce ordered
  fragments and a consistent `last` bit independently.
- Every received flit must name the local endpoint as its destination; a
  misrouted flit is consumed without an SRAM write and raises the sticky error.
- A context is released only when its last SRAM write is accepted and packet
  completion can be retained.
- Missing contexts, duplicate live keys, invalid counts, fragment-order errors,
  and inconsistent `last` values set sticky `protocol_error`.

## Performance-Model Correspondence

The RTL test compares every accepted TX flit's source, destination, VC, tag,
fragment, and `last` field with
`npu.sim.perf.noc_segmented_mesh.packetize_traffic_flow`. Payload bits come from
the SRAM response interface rather than the performance model's synthetic data
seed.

The block supports the current Phase 2 maximum of eight 256-bit fragments per
256-byte packet. The command scheduler remains responsible for collision-free
tag allocation and receive-context installation before release.

## Physical Scope

The L1 harness internally drives paired TX/RX descriptors, variable packet
lengths, all VCs, tags, destinations, SRAM stalls, completion stalls, and all
payload bits. Its PPA is an endpoint-control-plus-boundary-harness anchor.

It does not include SRAM bitcells/macros, a router, mesh wiring, producer or
reducer arithmetic, HBM/DRAM, or workload-matched switching activity.
