# Llama7B score32 exp-LUT divider composed datapath reduced-replica recost

This proposal adds one L2 composed-PPA recost task for the score32 exp-LUT divider datapath.

Item: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`  
Task type: `l2_campaign`  
Mode: `frontier_detail`  
Abstraction: `decoder_attention_composed_datapath_physical_feasibility`  
Comparison role: `score32_exp_lut_div_reduced_replica_recost`  
Baseline: `l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1_r2`

Dependencies:
- `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1` (expected L1 source id)
- `l2_decoder_attention_mixed_int8_score32_exp_lut_div_generation_quality_llama7b_v1`
- `l2_decoder_attention_composed_datapath_score32_w16_exact_div_reduced_replica_llama7b_v1_r2`

Execution is blocked until merged inputs and materialized references are present.
`run_physical` is `false` for this task.

Decision rule: recost the exp-LUT composed datapath **only after** the quality gate and L1 PPA dependencies are available; do not mark this as quality-backed unless the quality gate passes.
