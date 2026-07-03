# Llama7B score32 exp-LUT divider command-overhead recost

This proposal adds a dependency-gated L2 recost for the score32 exp-LUT divider
composed datapath with nonzero command-dispatch overhead.

Item: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1`
Task type: `l2_campaign`
Mode: `frontier_detail`
Abstraction: `decoder_attention_composed_datapath_physical_feasibility`
Comparison role: `score32_exp_lut_div_command_overhead_recost`

Dependencies:
- `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1`
- `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`

The recost sweeps command cycles per tile and per wave before applying the same
area-fit replica recost. It should not be treated as quality-backed unless the
referenced exp-LUT generation-quality gate passes.
