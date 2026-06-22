# Llama7B Measured Compute Closure with V3 Dense GEMM Metrics

This proposal stages an L2 rerank job that uses the merged `l1_npu_dense_gemm_tile_scaling_v3`
compute metrics to rebuild the Llama7B attention measured-compute frontier.

The rerank combines:

- source-backed HBM command-calibrated service,
- merged SRAM profile,
- corrected compute anchor from `l1_npu_dense_gemm_tile_scaling_v3`,
- and the PR #981 measured-compute frontier as the explicit comparison baseline.

The job is blocked until the L1 V3 merge is available and dispatches only on
`eval-daemon-b7c2d9c80c1c`.
