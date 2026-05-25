# Corrected NPU Compute Frontier

Canonical proposal workspace for `prop_l1_npu_corrected_compute_frontier_v1`.

The proposal rebuilds the FP16 NPU compute frontier after the GEMM/VEC
writeback connection fix.  The first item is a correctness guard; PPA items are
valid only after the guard passes.
