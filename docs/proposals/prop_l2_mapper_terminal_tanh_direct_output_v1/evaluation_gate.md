# Evaluation Gate

- lower-layer prerequisites merged:
  - `prop_l1_terminal_tanh_block_v1`
  - `prop_l1_npu_nm1_tanh_vec_enable_v1`
- next remote steps:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second
- do not queue the paired item until the baseline is merged and materialized
