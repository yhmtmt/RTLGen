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

## Capacity/HBM Gather Scheduler

- persistence: `transient`
- descriptors: `153` per layer, `4896` over 32 layers
- HBM source bytes per layer: `134217728`
- canonical bytes delivered per layer: `134217728`
- balanced delivery: `8388608` bytes per cluster
- Python/RTL descriptors and ready-valid stall stability: verified

## Required RTL Ownership

- external HBM-return ready/valid ingress boundary, excluding controller and PHY
- span-to-packet expansion and on-chip routing for HBM-return K/V bytes
- composition of capacity/HBM source descriptors with canonical K/V payload ingress
- backpressure from cluster SRAM and producers through ingress and mesh
- overlapped V transpose buffering selected from measured PPA
- physical cost of ping-pong K transpose and paired-dimension write control
- characterized SRAM macro substitution for inferred K/Q and cluster stores

## Next Gate

Compose the exact gather descriptors through shared-mesh source routing into canonical K/V ingress and verify end-to-end backpressure; then measure V buffering parallelism and substitute characterized SRAM macros.
