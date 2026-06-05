# Llama7B Dense Tile All-Measured Clustered Schedule

This proposal queues an L2 frontier-detail job that combines the measured dense
FP16 GEMM tile compute source with the existing Llama7B 131k clustered schedule
model and all-measured L1 local-cost profile.

The focused question is how the current Llama7B frontier moves when the schedule
uses measured dense compute tiles instead of the older nm-count compute blocks,
while still charging measured full-value attention datapath, softmax-weight
generator, FIFO, and router anchors.

The job consumes existing merged evidence only:

- `l1_npu_dense_gemm_tile_scaling_v2`
- `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- `l2_decoder_attention_sram_profile_v1`
- `l2_decoder_attention_noc_profile_v1`

SRAM capacity/service and global NoC arbitration remain analytic L2 terms. The
job records the materialized SRAM/NoC profile paths as calibration references so
the remaining abstraction is visible in the result.
