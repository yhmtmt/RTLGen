# Session Note

- proposal_id: `prop_cross_terminal_output_overlap_probe_v1`
- updated_utc: `2026-03-18T07:18:57+00:00`
- source_commit: `fdc37dcb665b91051f2987b0670f43db93906ceb`

## Current State

- direction gate: approved
- remote evaluation gate: not yet approved
- current stage: local overlap audit

## Local Audit Finding

- the accepted `nm1` baseline perf trace shows:
  - `SOFTMAX` from `493 ns` to `621 ns`
  - `dma_y` from `500 ns` to `564 ns`
- that means the terminal copy is hidden under the softmax tail in the current
  overlap model, which explains why removing `dma_y` produced no total-latency
  delta in PR `#41`

## Evidence Pointers

- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/artifacts/perf/fp16_nm1_softmax_r4/logistic_regression/trace.json`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/artifacts/mapper/fp16_nm1_softmax_r4/logistic_regression/schedule.yml`
- `npu/mapper/run.py`
- `npu/sim/perf/run.py`
- `npu/shell/spec.md`
- `npu/rtlgen/gen.py`

## Working Hypothesis

- this is likely not just a benchmark-shape issue
- the more immediate question is whether event signaling is intended to reflect
  command completion or merely descriptor issue order
- if signaling is not completion-bound today, then the current perf path can
  understate the benefit of removing `dma_y`

## Next Step

1. lock down the intended `EVENT_SIGNAL` / `EVENT_WAIT` contract
2. decide whether the follow-on work is:
   - a perf-model / shell-semantics correction, or
   - a benchmark-sensitivity rerun under the current semantics
3. only then request a new remote `{non-fused, fused}` campaign
