# Softmax-Recip HBM-Closed On-Chip Schedule

This proposal records the softmax-recip LUT variant of the HBM-closed on-chip
schedule closure for the Llama7B attention frontier.

The source frontier is
`l2_decoder_attention_kv_measured_hbm_service_softmax_recip_lut_llama7b_v1`.
The evaluation re-sweeps SRAM/NoC service knobs while keeping measured HBM
service, measured SRAM rebalance, softmax reciprocal LUT costs, and compute PPA
fixed.

The first result keeps the frontier at `2138.84136 us` and leaves
`tile_attention` dominant, so the next dependent job is the softmax-recip
subtile pipeline schedule.
