# Design Brief

## Structure
- Instantiate the exact `noc_segmented_mesh4x4` composition used by the Phase 2 cycle model.
- Retain 16 routers, 24 bidirectional neighbor pairs, four VCs, depth-four per-input VC FIFOs, and 256-bit flits.
- Generate full-width endpoint traffic internally to avoid exposing over 8,000 payload pins.
- Rotate each destination by an odd stride, cycle every VC, and vary every sink-ready signal.
- Register a distinct 16-bit payload slice plus metadata at each endpoint. Across 16 endpoints, all 256 payload bit positions remain observable without a global XOR or 16:1 mux path.

## Accounting
- Included: mesh routers, FIFOs, links, endpoint source state, compact observation registers, placement wiring, and clock distribution.
- Tool-dependent: diagnostic counter outputs are unobserved at the aggregate top, but hierarchical module retention may preserve their internal logic. The synthesis report must classify retained counter cost.
- Excluded: SRAM macros, HBM/DRAM, producer/finalizer datapaths, and workload-derived switching activity.
