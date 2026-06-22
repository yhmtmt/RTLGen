# Quality Gate

## Checks

- metric: structural MAC count
  - threshold: generated manifests report 256 MAC/cycle for `16x16 k1` and
    512 MAC/cycle for `16x16 k2`.
- metric: datapath connectivity
  - threshold: every generated MAC instance output folds into `result_hash`.
- metric: PPA output
  - threshold: each design records `metrics.csv` rows; failed rows are kept as
    boundary evidence rather than discarded.
- metric: comparison readiness
  - threshold: result rows are sufficient to compute MAC/cycle/mm2 and
    mW/(MAC/cycle), then feed the measured-compute Llama7B frontier rerank.

## Result

- status: pending
