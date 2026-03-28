# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `title`: `Softmax-tail fused tile path`

## Why This Gate Is Required
- This proposal changes the terminal softmax-tail lowering path.
- The current remote evaluation lane measures PPA and runtime, but that alone
  is insufficient for a change that can alter output tensors.
- For this specific proposal, the intended change is narrower than a new
  numerical backend: the softmax math should stay identical and only the final
  storage path should change.
- The quality gate therefore requires a bounded equivalence check before remote
  PPA spend is justified.

## Reference
- baseline_ref:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- reference_ref:
  - accepted softmax-tail baseline output path and the perf-sim softmax
    expected-result logic in `npu/sim/perf/run.py`

## Checks
- pre-softmax compute-path equivalence between baseline and candidate
  - threshold: `required`
- terminal `SOFTMAX` parameters unchanged (`src`, `row_bytes`, `rows`, `dtype`)
  - threshold: `required`
- candidate removes only the terminal `dma_y` hop and routes `SOFTMAX` directly
  to `Y_DRAM`
  - threshold: `required`
- perf trace delta bounded to removal of one DMA op and its transferred bytes
  - threshold: `required`

## Local Commands
- existing hook to reuse:
  - `python3 /workspaces/RTLGen/npu/sim/perf/run.py ...`
- existing softmax expected-result regression:
  - `python3 /workspaces/RTLGen/npu/sim/perf/tests/test_perf_vec_softmax.py`
- candidate-specific comparison command:
  - `python3 /workspaces/RTLGen/npu/eval/compare_terminal_softmax_quality.py --onnx /workspaces/RTLGen/runs/model_cache/onnx_imported_softmax_tail_v1/logistic_regression.onnx --baseline-arch /workspaces/RTLGen/npu/arch/examples/minimal.yml --candidate-arch /workspaces/RTLGen/npu/arch/examples/minimal_softmax_tail_fused.yml --perf-config /workspaces/RTLGen/npu/sim/perf/example_config_fp16_cpp.json --batch-override 256 --out-json /workspaces/RTLGen/docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report.json --out-md /workspaces/RTLGen/docs/proposals/prop_l2_softmax_tile_fusion_v1/quality_report.md`

## Result
- status: passed
- validated_utc: `2026-03-16T03:50:00Z`
- note: The proposal passed the bounded routing-equivalence quality check. The
  candidate keeps `dma_x`, `dma_w1`, `dma_b1`, and `gemm1` identical, keeps
  terminal `SOFTMAX` parameters identical, routes `softmax1` directly to
  `Y_DRAM`, and removes only the terminal `dma_y` hop. See
  `quality_report.json`, `quality_report.md`, and `quality_report_artifacts/`.
