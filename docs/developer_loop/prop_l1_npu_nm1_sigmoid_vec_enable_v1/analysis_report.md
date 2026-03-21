# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `candidate_id`: `l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r8`

## Evaluations Consumed
- upstream accepted prerequisite:
  - `prop_l1_terminal_sigmoid_block_v1`
  - merged evidence PR `#63`
  - accepted bounded `int8` sigmoid `pwl` wrapper point:
    - `critical_path_ns`: `0.1904`
    - `die_area`: `25600.0`
    - `total_power_mw`: `5.84e-05`
- integrated `nm1` sigmoid vec attempts:
  - `r1` to `r6`: setup/runtime failures while bringing up the integrated block
  - `r7`: fixed FloPoCo provisioning path, but failed because the integrated config
    pinned `binary_path` to `/workspaces/RTLGen/build/rtlgen`
  - PR `#66` merged and corrected the integrated config to use relative
    `build/rtlgen`
  - `r8`: now gets through `build_generator` and `generate_block_rtl`, but
    `run_block_sweep` on full `npu_top` stalls in long `abc` mapping

## Baseline Comparison
- baseline physical source for this proposal is the accepted standalone sigmoid
  wrapper from `prop_l1_terminal_sigmoid_block_v1`
- this proposal's added requirement is not sigmoid arithmetic legality itself,
  but an accepted integrated `nm1` physical point suitable for downstream Layer
  2 campaigns
- no accepted integrated `nm1` sigmoid block exists yet

## Result
- result: iterate
- confidence level: medium
- estimated optimization room: high
- circuit conclusion robustness: not yet sufficient for downstream Layer 2
  activation-family evaluation

## Failures and Caveats
- the standalone `int8` sigmoid block itself is no longer the blocker; it is
  accepted evidence
- the current blocker is physical-flow practicality for the integrated full
  `npu_top` target, especially long-running `abc` mapping inside
  `run_block_sweep`
- this exposed control-plane gaps:
  - no first-class run cancellation from the developer side
  - no stall timeout / long-command classification
  - no partial per-stage progress beyond lease heartbeats
- repeated retries on the same full-top sweep are not the right default until
  long-run controls and/or a smaller integrated proof target exist

## Recommendation
- keep the proposal active but do not promote yet
- land control-plane support for:
  - explicit cancel requests
  - command stall timeout and progress events
  - better long-run operator observability
- after that, either:
  - rerun the integrated `nm1` sweep with bounded runtime controls, or
  - define a smaller integrated physical proof target than full `npu_top`

## Next Reduced Sweep
- use `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidcmp/sweep_compare_33_firstpass.json` for the next attempt
- preserve `gemm_compute_array` and `vec_act_sigmoid_int8` hierarchy
- relax `CLOCK_PERIOD` to `12.0` and `PLACE_DENSITY` to `0.3`
