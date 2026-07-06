# Score32 exp-LUT Service Closure Audit

- decision: `score32_exp_lut_service_closure_recorded`
- score32 supported: `True`
- wrapper metrics match: `True`
- latency us: `12519.342352`
- MAC/cycle: `104320`
- remaining abstractions: `tile_local_and_shared_sram, hbm_dram_service`

## Components

| component | status | source |
|---|---|---|
| compute_datapath | measured | runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/metrics.csv |
| command_dispatch_control | measured | runs/designs/npu_blocks/attention_command_dispatch_c16_q32/metrics.csv |
| endpoint_ready_valid | measured_with_width_note |  |
| router_fifo_noc | measured_with_lane_replication |  |
| tile_local_and_shared_sram | measured_capacity_estimate | runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_local_sram_capacity__l2_decoder_attention_local_sram_capacity_llama7b_v1.json |
| hbm_dram_service | inherited_model | channel_burst_row_window_v1 |

## Next Step

- Use this score32 exp-LUT row as the quality-backed compute/service baseline, then close the inherited HBM/DRAM service or replace SRAM macro packing with a placed memory hierarchy.
