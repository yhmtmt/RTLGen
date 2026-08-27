# Implementation Summary

- Added a logic-free node-5 specialization of `noc_segmented_mesh_router`.
- Reused that exact top in the RTL/performance replay VCD.
- Added canonical source staging and a guard that rejects source divergence,
  added specialization state, or a broken Yosys hierarchy.
- Added Layer 1 task generation for direct `run_block_sweep.py` hardening.
- Added a three-utilization Nangate45 sweep at the measured 1.8 ns boundary.
