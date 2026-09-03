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

## Required RTL Ownership

- external HBM-return ready/valid ingress boundary, excluding controller and PHY
- capacity-driven resident-range descriptor and source selection
- planar gather descriptor generation for partial resident token ranges
- locality-aware tile-to-cluster scheduler preserving balanced waves
- on-chip packet routing for remote resident K/V bytes
- capacity/HBM source descriptor to canonical K/V tensor-address ingress
- backpressure from cluster SRAM and producers through ingress and mesh
- overlapped or multi-lane K/V transpose buffering selected from measured PPA
- characterized SRAM macro substitution for inferred K/Q and cluster stores

## Next Gate

Implement the capacity-driven resident/HBM gather scheduler and shared-mesh source routing, then measure K/V buffering parallelism and characterized SRAM substitution.
