# Llama7B Exact K/V Ingress Closure Audit

- decision: `historical_fractional_vc0_cannot_serve_as_exact_cluster_fill_contract`
- complete layer K/V: `134217728` bytes
- exact cluster V fills: `67108864` bytes
- exact cluster K stream: `67108864` bytes
- capacity-driven resident share per layer: `2228224` bytes
- historical remote VC0 bytes: `1949696` bytes

The historical VC0 quantity matches a capacity share in aggregate, but its fractional-smear contexts do not identify exact K/V tensor bytes and cannot be wired directly to cluster fill.

## One-Buffer Transpose Reference

- V block: `48` transfer cycles, target II `49`
- paired-stream K block: `192` transfer cycles, target II `193`
- K output writes the embodied 64-bank store; p53/p54 parallel readout is verified

## K Ingress Architecture Frontier

- one_buffer_serial: `12351` cycles/head, 1 buffer(s), 128-bit stage write, RTL verified `true`
- pingpong_serial: `8256` cycles/head, 2 buffer(s), 128-bit stage write, RTL verified `false`
- one_buffer_wide: `8255` cycles/head, 1 buffer(s), 256-bit stage write, RTL verified `false`
- pingpong_wide_auto: `4160` cycles/head, 2 buffer(s), 256-bit stage write, RTL verified `true`

## Required RTL Ownership

- external HBM-return ready/valid ingress boundary, excluding controller and PHY
- capacity-driven resident-range descriptor and source selection
- planar gather descriptor generation for partial resident token ranges
- locality-aware tile-to-cluster scheduler preserving balanced waves
- on-chip packet routing for remote resident K/V bytes
- capacity/HBM source descriptor to canonical K/V tensor-address ingress
- backpressure from cluster SRAM and producers through ingress and mesh
- overlapped V transpose buffering selected from measured PPA
- physical cost of ping-pong K transpose and paired-dimension write control
- characterized SRAM macro substitution for inferred K/Q and cluster stores

## Next Gate

Implement the capacity-driven resident/HBM gather scheduler and shared-mesh source routing, then measure V buffering parallelism, K ingress control PPA, and characterized SRAM substitution.
