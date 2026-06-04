# Quality Gate

## Checks
- metric: registry evidence
  - threshold: report must cite dense 8x8 measurement and dense-vs-nm64 claim.
- metric: measured best density
  - threshold: measured best source must be
    `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`.
- metric: frontier output
  - threshold: report must include compute ceiling, HBM floor, selected latency,
    and dominant resource by die, logic fraction, and density envelope.

## Result
- status: pending
