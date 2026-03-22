# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`

## Scope
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
- design a smaller integrated top or physical proxy below full `npu_top`
- queue the next real Layer 1 physical metrics item only after that reduced target is defined
