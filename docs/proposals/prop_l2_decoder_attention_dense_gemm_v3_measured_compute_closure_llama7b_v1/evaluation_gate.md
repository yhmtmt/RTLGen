# Evaluation Gate

- status: blocked_until_l1_v3_merged
- approved_by:
- approved_utc:
- allowed_evaluations:
  - `l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1`
- required_machine: `eval-daemon-b7c2d9c80c1c`
- note: Dispatch is blocked until `l1_npu_dense_gemm_tile_scaling_v3` is merged because
  this rerank depends on the V3 dense-GEMM compute rows.
