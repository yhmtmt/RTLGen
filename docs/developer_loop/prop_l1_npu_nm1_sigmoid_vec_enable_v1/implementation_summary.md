# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`
- `abstraction_layer`: `architecture_block`

## Scope
- generalized abstraction level: `architecture_block`
- bounded sigmoid support is implemented in the fixed `nm1` vec path
- one integrated sigmoid-enabled `nm1` block design/config is staged for Layer 1 evaluation
- the immediate blocker is no longer implementation correctness; it is obtaining a practical integrated physical proof target

## Local Validation
- local RTL/perf/control-plane smoke checks passed during bring-up of the integrated sigmoid-enabled `nm1` block
- remote Layer 1 attempts fixed two runtime issues:
  - FloPoCo provisioning/default build contract
  - integrated config `binary_path` for `rtlgen`
- the stable remote checkpoint is now `r14`, which proves:
  - `build_generator` succeeds
  - `generate_block_rtl` succeeds
  - `1_1_yosys_canonicalize` succeeds on the integrated design
- later stages remain impractical on the full-top target:
  - `r15`: `1_2_yosys` timed out
  - `r16`: direct `yosys_stats_prefilter` experiment was buggy and has been abandoned

## Evaluation Request
- current accepted checkpoint for this proposal is synth-only, not physical:
  - `r14` / PR `#69`
  - `evaluation_mode = synth_prefilter`
- next local step is not another full `npu_top` retry
- next local step is to define a reduced integrated physical proxy that preserves the sigmoid vec path and enough surrounding fabric to be architecturally meaningful

## Next Reduced Target
- keep the existing canonicalize prefilter as the legality gate before physical spend
- the reduced integrated proxy is now defined as:
  - design: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidproxy`
  - config: `config_nm1_sigmoidproxy.json`
  - sweep: `sweep_proxy_firstpass.json`
- the proxy preserves the fixed `nm1` GEMM plus sigmoid vec path while removing
  shell-facing DMA/CQ/AXI/MMIO wrapper overhead and SRAM integration
- next real Layer 1 physical metrics item should target this reduced proxy
  rather than full `npu_top`
