# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- `title`: `NPU nm1 sigmoid vec enable`
- `abstraction_layer`: `architecture_block`

## Scope
- generalized abstraction level: `architecture_block`
- bounded sigmoid support is implemented in the fixed `nm1` vec path
- the accepted first-pass physical source is the reduced integrated proxy `npu_fp16_cpp_nm1_sigmoidproxy`
- this closes the architecture-block prerequisite for downstream Layer 2 activation-family work

## Local Validation
- local RTL/perf/control-plane smoke checks passed during bring-up of the integrated sigmoid-enabled `nm1` block
- remote Layer 1 attempts fixed two runtime issues:
  - FloPoCo provisioning/default build contract
  - integrated config `binary_path` for `rtlgen`
- accepted remote checkpoints are now:
  - `r14`: integrated legality/synth-prefilter checkpoint at `1_1_yosys_canonicalize`
  - `r18`: reduced-proxy physical metrics checkpoint accepted by merged PR `#74`

## Accepted Physical Source
- design: `runs/designs/npu_blocks/npu_fp16_cpp_nm1_sigmoidproxy`
- config: `config_nm1_sigmoidproxy.json`
- sweep: `sweep_proxy_firstpass.json`
- accepted best point:
  - `param_hash`: `b5526579`
  - `critical_path_ns`: `2.7883`
  - `die_area`: `1440000.0`
  - `total_power_mw`: `0.00036`

## Follow-on
- use this accepted `architecture_block` source to unblock `prop_l2_mapper_terminal_activation_family_v1`
- do not reopen full `npu_top` integrated physical attempts as a prerequisite for the next bounded Layer 2 activation-family measurement item

- policy update: early-stage `architecture_block` sweeps now reject `mode_compare` / `flat_nomacro` and require hierarchy-preserving first-pass configs
