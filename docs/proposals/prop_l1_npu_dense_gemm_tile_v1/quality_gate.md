# Quality Gate

## Checks
- metric: structural MAC count
  - threshold: generated manifest must report 16 MAC/cycle for `4x4` and
    64 MAC/cycle for `8x8`.
- metric: datapath connectivity
  - threshold: every generated MAC instance output must fold into
    `result_hash`.
- metric: PPA output
  - threshold: each design records `metrics.csv` rows, with failures preserved
    as boundary evidence if timing or flow fails.
- metric: comparison readiness
  - threshold: result must be sufficient to compute MAC/cycle/mm2 and compare
    against `rtlgen_npu_fp16_nm64_flat_cmp33_nangate45`.

## Result
- status: pending
