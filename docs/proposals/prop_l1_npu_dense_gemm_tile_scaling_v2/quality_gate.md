# Quality Gate

## Checks
- metric: structural MAC count
  - threshold: generated manifest must report 128 MAC/cycle for `8x16` and
    `16x8`, and 256 MAC/cycle for `16x16`.
- metric: datapath connectivity
  - threshold: every generated MAC instance output must fold into
    `result_hash`.
- metric: PPA output
  - threshold: each design records `metrics.csv` rows, with failures preserved
    as boundary evidence if timing or flow fails.
- metric: comparison readiness
  - threshold: result must be sufficient to compute MAC/cycle/mm2 and compare
    against `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`.

## Result
- status: pending
