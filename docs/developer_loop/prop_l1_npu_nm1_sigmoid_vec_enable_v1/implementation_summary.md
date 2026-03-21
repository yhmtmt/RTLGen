# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`

## Scope
- bounded sigmoid support is now implemented in the fixed `nm1` vec path
- one integrated sigmoid-enabled `nm1` block design/config is staged for Layer 1
  physical evaluation
- the immediate blocker is not feature implementation anymore, but practical
  physical-flow execution for the full `npu_top` proof target

## Local Validation
- local RTL/perf/control-plane smoke checks passed during bring-up of the
  integrated sigmoid-enabled `nm1` block
- remote Layer 1 attempts exposed two runtime issues that are now fixed:
  - FloPoCo provisioning/default build contract
  - integrated config `binary_path` for `rtlgen`
- the remaining problem is long-duration `abc` mapping during full-top sweep
- first runtime-bounded retry `r9` confirmed the issue is a `run_block_sweep` stall, not worker death: the command was classified as stalled after 300s without new output
- next proof target should therefore be a cheaper first-pass integrated sweep that preserves both `gemm_compute_array` and `vec_act_sigmoid_int8` and relaxes timing/floorplan pressure

## Evaluation Request
- remote attempts have reached `run_block_sweep` successfully
- `r9` validated the new control-plane runtime controls: `run_block_sweep` now terminates as `TIMED_OUT` with `stalled=true` instead of hanging indefinitely
- next local step:
  - use `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/sweep_compare_33_firstpass.json` as the next integrated proof target
  - if that cheaper first-pass target still stalls, split the sweep further or add a synth-only prefilter before another full OpenROAD spend
