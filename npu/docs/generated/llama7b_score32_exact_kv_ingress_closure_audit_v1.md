# Llama7B Exact K/V Ingress Closure Audit

- decision: `historical_fractional_vc0_cannot_serve_as_exact_cluster_fill_contract`
- complete layer K/V: `134217728` bytes
- exact cluster V fills: `67108864` bytes
- exact cluster K stream: `67108864` bytes
- capacity-driven resident share per layer: `2228224` bytes
- historical remote VC0 bytes: `1949696` bytes

The historical VC0 quantity matches a capacity share in aggregate, but its fractional-smear contexts do not identify exact K/V tensor bytes and cannot be wired directly to cluster fill.

## Required RTL Ownership

- external HBM-return ready/valid ingress boundary, excluding controller and PHY
- capacity-driven resident-range descriptor and source selection
- locality-aware tile-to-cluster scheduler preserving balanced waves
- on-chip packet routing for remote resident K/V bytes
- K/V tensor address decoder and partial-packet byte validity
- 1KiB token-major-to-fill-row V transpose buffer and assembler
- 2KiB paired-stream K transpose buffer, producer-beat assembler, and p53/p54 slot distributor
- per-cluster fill target, double-buffer residency, and command release
- backpressure from cluster SRAM and producers through ingress and mesh

## Next Gate

Implement and verify the canonical tensor-address decoder plus representative p54/p53 K/V transpose assemblers before composing capacity-driven NoC/HBM source scheduling.
