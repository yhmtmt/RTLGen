# Implementation Summary

## Proposal
- `proposal_id`: `prop_cross_terminal_output_overlap_probe_v1`
- `title`: `Terminal-output overlap probe`

## Scope
- changed:
  - tightened perf overlap scheduling so `EVENT_SIGNAL` in overlap mode does
    not become visible before the immediately preceding producer op completes
  - added a regression proving `GEMM -> EVENT_SIGNAL -> EVENT_WAIT -> DMA_COPY`
    cannot issue the DMA before the GEMM completes
  - reran the accepted `nm1` baseline descriptor stream locally with the updated
    simulator to quantify how much terminal-copy cost had been hidden
- not changed:
  - no Layer 1 or Layer 2 hardware
  - no mapper lowering
  - no remote campaign request yet
  - no control-plane behavior

## Files Changed
- `npu/sim/perf/run.py`
- `npu/sim/perf/tests/test_perf_basic.py`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/design_brief.md`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/evaluation_gate.md`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/evaluation_requests.json`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/proposal.json`
- `docs/developer_loop/prop_cross_terminal_output_overlap_probe_v1/session_note.md`

## Local Validation
- commands run:
  - `python3 npu/sim/perf/tests/test_perf_basic.py`
  - `python3 npu/sim/perf/tests/test_perf_vec_softmax.py`
  - `python3 npu/sim/perf/run.py --bin runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/artifacts/mapper/fp16_nm1_softmax_r4/logistic_regression/descriptors.bin --out /tmp/nm1_overlap_trace_after_fix.json --config npu/sim/perf/example_config_fp16_cpp.json --overlap`
- result:
  - targeted perf tests passed
  - the local rerun of the accepted `nm1` baseline moved terminal `dma_y` after
    `SOFTMAX` completion and increased total simulated latency from the old
    `621 ns` trace result to `967.75 ns`

## Evaluation Request
- requested remote tasks: none yet
- cost class: pending
- baseline to compare against:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1`
- gate before remote spend:
  - confirm that completion-bound event semantics are the intended contract for
    the shell/perf path
  - then choose whether to request a new focused `{non-fused, fused}` rerun or
    split the simulator/contract correction into its own proposal

## Risks
- the shell RTL stub and written shell spec still need alignment review with the
  updated perf behavior
- this local result reinterprets earlier accepted campaign traces, so any remote
  rerun will need clear baseline-delta explanation
- if the shell contract intentionally allows immediate event signaling, then the
  new perf behavior is too strict and this work should be reframed as a model
  divergence investigation rather than a fix
