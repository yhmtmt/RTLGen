# L1 score32 exp-LUT divider composed datapath PPA

This proposal measures the concrete composed dual-stream datapath for
`score32_exp_lut_div`:

- config: `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/config.json`
- sweep: `runs/campaigns/npu/attention_dual_stream_composed_v1/sweeps/nangate45_dual_stream_composed_hier_score32_w16_exp_lut_div_b20.json`
- item: `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1`

The run measures local Nangate45 PPA only. The result becomes eligible for
Llama7B reduced-replica recost only after the matching generation-quality gate
is available.
