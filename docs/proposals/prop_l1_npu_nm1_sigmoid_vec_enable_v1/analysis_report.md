# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `candidate_id`: `l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r18`
- `abstraction_layer`: `architecture_block`

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
  - `r18`: reduced proxy physical sweep succeeded and was accepted by merged PR `#74`

## Baseline Comparison
- baseline physical source for this proposal is the accepted standalone sigmoid wrapper from `prop_l1_terminal_sigmoid_block_v1`
- this proposal's added requirement was an accepted integrated `nm1` physical point suitable for downstream Layer 2 campaigns
- accepted integrated best point from the merged evidence:
  - `param_hash`: `b5526579`
  - `critical_path_ns`: `2.7883`
  - `die_area`: `1440000.0`
  - `total_power_mw`: `0.00036`
  - `metrics_csv`: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidproxy/metrics.csv`

## Result
- result: accepted first-pass integrated sigmoid-enabled `nm1` architecture-block source
- confidence level: medium
- estimated optimization room: moderate
- circuit conclusion robustness: sufficient to unblock downstream Layer 2 activation-family measurement-first work

## Failures and Caveats
- the accepted result comes from the reduced integrated proxy `npu_fp16_cpp_nm1_sigmoidproxy`, not full `npu_top`
- the reduced proxy preserves the fixed `nm1` GEMM plus sigmoid vec path while intentionally removing shell-facing DMA/CQ/AXI/MMIO wrapper overhead and SRAM integration
- this is sufficient as an `architecture_block` physical source for the next bounded Layer 2 activation-family campaign, but it is not yet a claim about full-top `nm1` feasibility under the same flow budget
- the earlier `r14` canonicalize checkpoint remains useful as a legality gate history, but the proposal is now grounded on real physical metrics from `r18`

## Recommendation
- promote this integrated sigmoid-enabled `nm1` source as the accepted `architecture_block` prerequisite for `prop_l2_mapper_terminal_activation_family_v1`
- queue the Layer 2 `measurement_only` bounded activation-family reference item next, using the accepted reduced proxy as the lower-layer physical grounding
