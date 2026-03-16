# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `title`: `Softmax-tail fused tile path`

## Why This Gate Is Required
- This proposal changes the terminal softmax-tail lowering path.
- The current remote evaluation lane measures PPA and runtime, but that alone
  is insufficient for a change that can alter output tensors.
- This candidate must show acceptable output agreement before remote PPA spend
  is justified.

## Reference
- baseline_ref:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- reference_ref:
  - accepted softmax-tail baseline output path and the perf-sim softmax
    expected-result logic in `npu/sim/perf/run.py`

## Checks
- exact top-1 class agreement on the imported softmax-tail model set
  - threshold: `100%`
- terminal softmax output byte agreement against the accepted baseline or
  software reference
  - threshold: `max_abs_err <= 1 LSB`
- no missing expected-result generation for terminal `SOFTMAX` events in the
  perf trace
  - threshold: `required`

## Local Commands
- existing hook to reuse:
  - `python3 /workspaces/RTLGen/npu/sim/perf/run.py ...`
- existing softmax expected-result regression:
  - `python3 /workspaces/RTLGen/npu/sim/perf/tests/test_perf_vec_softmax.py`
- candidate-specific comparison command:
  - pending implementation

## Result
- status: pending
- note: Remote Layer 2 PPA evaluation is blocked until a candidate-specific output-quality comparison command is wired and passes these checks.
