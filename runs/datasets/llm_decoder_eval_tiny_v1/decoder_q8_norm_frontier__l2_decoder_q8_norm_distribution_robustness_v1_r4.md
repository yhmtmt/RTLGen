# Decoder q8 Normalization Frontier

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_robustness_v1_r4.json`
- decision: `measured_frontier_candidate_selected`
- selected_candidate: `grid_approx_pwl_bf16_path`
- reason: grid_approx_pwl_bf16_path preserved the exact prompt-stress gate and has the best measured_bf16_reciprocal_datapath_ppa among exact-safe measured normalization candidates. The best exact-safe q8 reciprocal row remains grid_approx_pwl_in_q8_w_q8_norm_recip_q10.
- cost_model_source: `rtlgen_openroad_q8_exact_q8_reciprocal_and_bf16_reciprocal_datapath_metrics`
- cost_model_unit: `nangate45_physical_metrics`
- rtlgen_calibration_proposal: `prop_l1_decoder_q8_recip_norm_datapath_v1_and_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_and_prop_l1_decoder_bf16_recip_norm_datapath_v1`

## Cost Model Provenance

Measured q8 exact, q8 reciprocal, and bf16 reciprocal candidates are ranked lexicographically by critical path, then area, then power. These physical metrics are comparable only within the current Nangate45 row-8 normalization datapath framing.

Replace the q8 normalization heuristic with merged RTLGen/OpenROAD datapath evidence and compare it with the measured bf16 reciprocal anchor while preserving quality gates from the decoder sweep.

## Quality And Normalization PPA

| template | role | gate | next-token | top-k | norm mode | recip bits | rank source | critical_path_ns | die_area | total_power_mw |
|---|---|---|---:|---:|---|---:|---|---:|---:|---:|
| `grid_approx_pwl_bf16_path` | `bf16_primary_anchor` | `exact_safe_survivor` | 12/12 | 12/12 | `reciprocal_float` |  | `measured_bf16_reciprocal_datapath_ppa` | 4.2869 | 50690.271025 | 0.00479 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 12/12 | 12/12 | `reciprocal_quantized` | 10 | `measured_q8_reciprocal_datapath_ppa` | 5.6126 | 39776.3136 | 0.00463 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 12/12 | 12/12 | `reciprocal_quantized` | 12 | `measured_q8_reciprocal_datapath_ppa` | 5.7554 | 52118.607025 | 0.014 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 12/12 | 12/12 | `reciprocal_quantized` | 14 | `measured_q8_reciprocal_datapath_ppa` | 5.7617 | 52360.880625 | 0.00637 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 12/12 | 12/12 | `reciprocal_quantized` | 16 | `measured_q8_reciprocal_datapath_ppa` | 5.814 | 45315.765625 | 0.0321 |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `q8_exact_normalization_baseline` | `exact_safe_survivor` | 12/12 | 12/12 | `exact` |  | `measured_q8_exact_datapath_ppa` | 20.2712 | 105898.1764 | 1.11 |

## Blocked Rows

- none

## Next Step

- Treat the bf16 and q8 reciprocal measurements as current row-8 Nangate45 datapath evidence, not distribution-robust architecture proof.
- Broaden weight/input distribution coverage before making a final q8-versus-bf16 normalization decision.
