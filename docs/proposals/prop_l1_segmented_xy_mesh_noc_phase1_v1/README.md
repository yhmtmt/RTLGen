# Segmented XY Mesh NoC Phase 1

This proposal materializes the first concrete NoC RTL block beyond the earlier synthetic router anchor: a synthesizable 256-bit deterministic-XY router with five ports, four virtual channels, per-input/per-VC buffering, fair arbitration, and a matching cycle model checked against RTL.

The deliverables here are intentionally bounded:
- concrete router RTL and 4x4 mesh composition under `npu/sim/rtl`
- a cycle model under `npu/sim/perf`
- focused RTL/model/generator tests
- a PPA-ready single-router wrapper config for Nangate45

The remaining abstraction after this phase is the full scheduled workload on top of the mesh and the physical aggregate placement of the complete 4x4 network.
