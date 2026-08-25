# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- Materialize segmented deterministic-XY NoC Phase 1 router and cycle model.

## Scope
- Added segmented router primitive support to `l1_memory_noc_primitive`.
- Added a PPA-ready single-router config and dedicated Nangate45 sweep.
- Added a cycle model for the segmented router/mesh under `npu/sim/perf`.
- Added focused generator, router RTL/model, and mesh RTL/model tests.
- Revised the physical source harness to advance independent full-width flit state. The earlier 32-bit seed assignment left the upper 224 bits constant and was invalid for a 256-bit physical datapath claim.
- Reworked round-robin arbitration after the r4 physical attempt exposed synthesis resource explosion. Route requests are decoded once into narrow bits, round-robin selection scans those bits, and each output selects the 274-bit buffered flit once after grant selection. The prior loop dynamically selected and decoded a wide flit for every output/input scan candidate.

## Files Changed
- `scripts/generate_design.py`
- `examples/about_config.md`
- `npu/sim/perf/noc_segmented_mesh.py`
- `npu/sim/rtl/noc_segmented_mesh_router.sv`
- `npu/sim/rtl/noc_segmented_mesh4x4.sv`
- `tests/test_noc_segmented_mesh.py`
- `runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/config_l1_noc_segmented_xy_router_p5_w256_vc4_d4.json`
- `runs/campaigns/noc/l1_segmented_xy_mesh_router/sweeps/nangate45_macro_frontier.json`
- `docs/proposals/prop_l1_segmented_xy_mesh_noc_phase1_v1/`

## Local Validation
- `python3 scripts/generate_design.py runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/config_l1_noc_segmented_xy_router_p5_w256_vc4_d4.json nangate45 --force_gen True`
- `iverilog -g2012 -s l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper -t null /orfs/flow/designs/src/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/noc_ready_valid_fifo.v /orfs/flow/designs/src/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/noc_segmented_mesh_router.v /orfs/flow/designs/src/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/l1_noc_segmented_xy_router_p5_w256_vc4_d4.v /orfs/flow/designs/src/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper.v`
- `pytest -q tests/test_noc_segmented_mesh.py`
- Cycle/model regression after bounded-arbiter rewrite: `10 passed` (the direct generator test remains environment-dependent on writable `/orfs/flow/designs/src`).
- Bounded local Yosys `synth -noabc` probe: rewritten arbiter completed in 30.5 seconds at 880,536 KiB maximum RSS. The r4/master implementation exceeded 10,211,420 KiB after 98 seconds and was terminated while still growing; the remote r4 run peaked near 24.1 GiB and produced no physical rows.

## Remaining Abstractions
- The PPA top includes source/sink boundary state and observability counters. Its area and power are therefore a conservative router-plus-harness anchor rather than isolated-router accounting; the routed critical path still exercises the concrete router datapath.
- The physical evidence is still a single-router primitive, not the placed aggregate 4x4 mesh.
- The cycle model is exact for the focused routed/stalled scenarios covered here, but full workload scheduling on the mesh is still a separate step.
- SRAM/HBM traffic mapping and command scheduling remain above this transport phase.
