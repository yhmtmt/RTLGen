# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `abstraction_layer`: `architecture_block`
- current stable checkpoint: `l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r14`

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
  - `r7`: fixed FloPoCo provisioning path, but failed because the integrated config pinned `binary_path` to `/workspaces/RTLGen/build/rtlgen`
  - PR `#66` merged and corrected the integrated config to use relative `build/rtlgen`
  - `r8` and `r9`: full `npu_top` `run_block_sweep` proved impractical; `r9` validated the new stall/progress controls by classifying the command as stalled instead of hanging indefinitely
  - `r11` and `r12`: hierarchy-reduced full-top sweeps still exceeded the hard timeout budget
  - `r14`: accepted synth-prefilter checkpoint at `1_1_yosys_canonicalize`; integrated RTL generation and canonicalization both succeed
  - `r15`: `1_2_yosys` still times out at the full-top scale
  - `r16`: experimental direct `yosys_stats_prefilter` path failed immediately due to an implementation bug and is not accepted evidence

## Baseline Comparison
- baseline physical source for this proposal is the accepted standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1`
- this proposal's added requirement is not sigmoid arithmetic legality itself, but an accepted integrated `nm1` physical point suitable for downstream Layer 2 campaigns
- no accepted integrated `nm1` sigmoid physical point exists yet

## Result
- result: iterate
- confidence level: medium
- estimated optimization room: high
- circuit conclusion robustness: not yet sufficient for downstream Layer 2 activation-family evaluation

## Failures and Caveats
- the standalone `int8` sigmoid block itself is accepted evidence and no longer the blocker
- the current blocker is practical full-top synthesis cost for the integrated `npu_top` target
- the stable integrated checkpoint is only `r14` (`synth_prefilter` at canonicalize), not physical metrics
- the direct `yosys_stats_prefilter` experiment from `r16` was a buggy side path and has been backed out

## Recommendation
- keep the proposal active but do not promote yet
- treat `r14` / PR `#69` as the current stable integrated checkpoint
- do not spend more cycles on full `npu_top` synth/OpenROAD retries under the current proof target
- next technical step is to define a reduced integrated physical proxy that still includes the sigmoid vec path in realistic context, then queue a real physical metrics item against that smaller target

## Next Step
- retain the canonicalize prefilter path as the current legality gate
- design a reduced integrated proof target below full `npu_top`
- once that proxy target is defined, queue a new `measurement_only` Layer 1 physical sweep for real PPA
