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

## Evaluation Request
- remote attempts have reached `run_block_sweep` successfully
- next local step:
  - land control-plane long-run controls for cancel/stall/progress
  - then re-run the integrated Layer 1 sweep under those controls
  - if runtime is still impractical, reduce the physical proof target before
    spending more evaluator time
