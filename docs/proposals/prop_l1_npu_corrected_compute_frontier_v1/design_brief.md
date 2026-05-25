# Design Brief

- `proposal_id`: `prop_l1_npu_corrected_compute_frontier_v1`
- scope: corrected FP16 NPU compute parallelism frontier
- precondition: full-path RTL/perf architectural writeback equivalence and
  generated RTL module-retention guard

The previous pre-fix measurements can no longer drive architecture decisions.
This proposal uses the corrected writeback-connected RTL and keeps the
correctness guard as an explicit dependency of subsequent PPA sweeps.
