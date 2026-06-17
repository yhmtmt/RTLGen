# Reciprocal-LUT Endpoint Ready/Valid Service

This proposal closes one abstraction layer below the corrected Llama7B reciprocal-LUT
endpoint full on-chip service frontier.

The source frontier is:

- item: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2`
- selected profile: `hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12`
- selected architecture: `mesh2d_locality_aware_cluster_tree_c16_b64_dense_gemm_16x8_k1_p1`

The requested job derives concrete `onchip_service_endpoint` ready/valid queue
parameters from that frontier and runs the finite-queue/backpressure probe.
