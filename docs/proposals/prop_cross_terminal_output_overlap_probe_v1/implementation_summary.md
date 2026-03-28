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
  - fixed the generated shell stub so `EVENT_SIGNAL`/`EVENT_WAIT` now follow the
    same completion-bound contract instead of behaving as immediate queue-level
    markers
  - added a focused RTL regression for
    `DMA_COPY -> EVENT_SIGNAL -> EVENT_WAIT -> DMA_COPY`
- not changed:
  - no Layer 1 or Layer 2 hardware
  - no mapper lowering
  - no remote campaign request yet
  - no control-plane behavior

## Files Changed
- `npu/sim/perf/run.py`
- `npu/sim/perf/tests/test_perf_basic.py`
- `npu/rtlgen/gen.py`
- `npu/rtlgen/out/top.v`
- `npu/rtlgen/out/top_axi.v`
- `npu/rtlgen/out_cpp_mac/top.v`
- `npu/rtlgen/out_cpp_mac/top_axi.v`
- `npu/sim/rtl/tb_npu_shell.sv`
- `npu/shell/spec.md`
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/design_brief.md`
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/evaluation_gate.md`
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/evaluation_requests.json`
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/proposal.json`
- `docs/proposals/prop_cross_terminal_output_overlap_probe_v1/session_note.md`

## Local Validation
- commands run:
  - `python3 npu/sim/perf/tests/test_perf_basic.py`
  - `python3 npu/sim/perf/tests/test_perf_vec_softmax.py`
  - `python3 tests/test_npu_rtlgen_softmax.py`
  - `iverilog -g2012 -I npu/rtlgen/out -s tb_npu_shell -o /tmp/tb_npu_shell_event_dma.vvp npu/rtlgen/out/top.v npu/sim/rtl/tb_npu_shell.sv npu/sim/rtl/axi_mem_router.sv npu/sim/rtl/axi_mem_model.sv npu/rtlgen/out/sram_models.sv && vvp /tmp/tb_npu_shell_event_dma.vvp +event_dma_test=1`
  - `python3 npu/sim/perf/run.py --bin runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/artifacts/mapper/fp16_nm1_softmax_r4/logistic_regression/descriptors.bin --out /tmp/nm1_overlap_trace_after_fix.json --config npu/sim/perf/example_config_fp16_cpp.json --overlap`
- result:
  - targeted perf tests passed
  - targeted RTL shell regression passed
  - the local rerun of the accepted `nm1` baseline moved terminal `dma_y` after
    `SOFTMAX` completion and increased total simulated latency from the old
    `621 ns` trace result to `967.75 ns`

## Evaluation Request
- requested remote tasks:
  - one focused `{non-fused, fused}` Layer 2 rerun on the fixed `nm1` baseline
    under the corrected event contract
- cost class: medium
- baseline to compare against:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1`
- gate before remote spend:
  - regenerate the focused fused-output campaign on a commit that contains both
    the perf and shell event fixes
  - keep the direct comparison limited to the accepted `nm1` baseline vs fused
    `nm1` candidate

## Risks
- this local result reinterprets earlier accepted campaign traces, so any remote
  rerun will need clear baseline-delta explanation
- broader architecture ranking should still remain out of scope until the new
  focused rerun answers the fused-output mechanism question
