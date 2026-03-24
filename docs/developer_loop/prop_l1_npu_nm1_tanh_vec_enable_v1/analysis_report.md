# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- `candidate_id`: `l1_prop_l1_npu_nm1_tanh_vec_enable_v1_r2`
- `abstraction_layer`: `architecture_block`

## Evaluations Consumed
- upstream accepted prerequisite:
  - `prop_l1_terminal_tanh_block_v1`
  - merged evidence PR `#80`
  - accepted bounded `int8` tanh `pwl` wrapper point:
    - `critical_path_ns`: `0.1899`
    - `die_area`: `25600.0`
    - `total_power_mw`: `0.000111`
- integrated `nm1` tanh vec attempts:
  - `r1`: failed before execution because of a bad full source SHA
  - `r2`: reduced proxy physical sweep succeeded and was accepted by merged PR `#81`

## Baseline Comparison
- baseline physical source for this proposal is the accepted standalone tanh wrapper from `prop_l1_terminal_tanh_block_v1`
- this proposal's added requirement was an accepted integrated `nm1` physical point suitable for downstream Layer 2 campaigns
- accepted integrated best point from the merged evidence:
  - `param_hash`: `bf5fc187`
  - `critical_path_ns`: `2.8082`
  - `die_area`: `1440000.0`
  - `total_power_mw`: `0.000358`
  - `metrics_csv`: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/metrics.csv`

## Result
- result: accepted first-pass integrated tanh-enabled `nm1` architecture-block source
- confidence level: medium
- estimated optimization room: moderate
- circuit conclusion robustness: sufficient to unblock downstream bounded Layer 2 tanh work

## Failures and Caveats
- the accepted result comes from the reduced integrated proxy `npu_fp16_cpp_nm1_tanhproxy`, not full `npu_top`
- the reduced proxy preserves the fixed `nm1` GEMM plus tanh vec path while intentionally removing shell-facing DMA/CQ/AXI/MMIO wrapper overhead and SRAM integration
- this is sufficient as an `architecture_block` physical source for the next bounded Layer 2 tanh campaign, but it is not yet a claim about full-top `nm1` feasibility under the same flow budget

## Recommendation
- promote this integrated tanh-enabled `nm1` source as the accepted `architecture_block` prerequisite for the next bounded terminal `tanh` Layer 2 work
- keep that next work measurement-first and grounded on this reduced proxy source
