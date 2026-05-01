# Decoder q8 Normalization Frontier

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json`
- decision: `keep_q8_exact_or_bf16_anchor`
- selected_candidate: ``
- reason: No q8 reciprocal-normalization row preserved both next-token and top-k on every prompt-stress sample. Keep q8 exact normalization as the q8 quality baseline and bf16 reciprocal PWL as the primary anchor.
- cost_model_source: `rtlgen_openroad_q8_exact_q8_reciprocal_and_bf16_reciprocal_datapath_metrics`
- cost_model_unit: `nangate45_physical_metrics`
- rtlgen_calibration_proposal: `prop_l1_decoder_q8_recip_norm_datapath_v1_and_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_and_prop_l1_decoder_bf16_recip_norm_datapath_v1`

## Cost Model Provenance

Measured q8 exact, q8 reciprocal, and bf16 reciprocal candidates are ranked lexicographically by critical path, then area, then power. These physical metrics are comparable only within the current Nangate45 row-8 normalization datapath framing.

Replace the q8 normalization heuristic with merged RTLGen/OpenROAD datapath evidence and compare it with the measured bf16 reciprocal anchor while preserving quality gates from the decoder sweep.

## Quality And Normalization PPA

| template | role | gate | next-token | top-k | norm mode | recip bits | rank source | critical_path_ns | die_area | total_power_mw |
|---|---|---|---:|---:|---|---:|---|---:|---:|---:|
| `grid_approx_pwl_bf16_path` | `bf16_primary_anchor` | `topk_safe_not_exact` | 46/48 | 48/48 | `reciprocal_float` |  | `measured_bf16_reciprocal_datapath_ppa` | 4.2869 | 50690.271025 | 0.00479 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | `q8_reciprocal_candidate` | `topk_safe_not_exact` | 46/48 | 48/48 | `reciprocal_quantized` | 10 | `measured_q8_reciprocal_datapath_ppa` | 5.6126 | 39776.3136 | 0.00463 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | `q8_reciprocal_candidate` | `topk_safe_not_exact` | 46/48 | 48/48 | `reciprocal_quantized` | 12 | `measured_q8_reciprocal_datapath_ppa` | 5.7554 | 52118.607025 | 0.014 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` | `q8_reciprocal_candidate` | `topk_safe_not_exact` | 46/48 | 48/48 | `reciprocal_quantized` | 14 | `measured_q8_reciprocal_datapath_ppa` | 5.7617 | 52360.880625 | 0.00637 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` | `q8_reciprocal_candidate` | `topk_safe_not_exact` | 46/48 | 48/48 | `reciprocal_quantized` | 16 | `measured_q8_reciprocal_datapath_ppa` | 5.814 | 45315.765625 | 0.0321 |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `q8_exact_normalization_baseline` | `topk_safe_not_exact` | 46/48 | 48/48 | `exact` |  | `measured_q8_exact_datapath_ppa` | 20.2712 | 105898.1764 | 1.11 |

## Blocked Rows

- `grid_approx_pwl_bf16_path`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q12`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q14`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`
- `grid_approx_pwl_in_q8_w_q8_norm_recip_q16`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`
- `grid_approx_pwl_in_q8_w_q8_norm_exact`: next misses `dist2_arith_three_plus_five, dist2_sequence_months`, top-k misses `none`

## Next Step

- Treat the bf16 and q8 reciprocal measurements as current row-8 Nangate45 datapath evidence, not distribution-robust architecture proof.
- Broaden weight/input distribution coverage before making a final q8-versus-bf16 normalization decision.
