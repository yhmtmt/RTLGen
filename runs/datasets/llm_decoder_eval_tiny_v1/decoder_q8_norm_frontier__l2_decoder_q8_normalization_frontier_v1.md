# Decoder q8 Normalization Frontier

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_normalization_frontier_v1.json`
- decision: `q8_reciprocal_candidate_survived`
- selected_candidate: `grid_approx_pwl_in_q8_w_q8_norm_recip_q10`
- reason: grid_approx_pwl_in_q8_w_q8_norm_recip_q10 preserved the exact prompt-stress gate and has the best measured_q8_reciprocal_datapath_ppa among exact-safe q8 reciprocal candidates. q8 exact and bf16 reciprocal normalization remain unmeasured hardware gaps.
- cost_model_source: `rtlgen_openroad_q8_reciprocal_datapath_metrics`
- cost_model_unit: `nangate45_physical_metrics`
- rtlgen_calibration_proposal: `prop_l1_decoder_q8_recip_norm_datapath_v1`

## Cost Model Provenance

Measured q8 reciprocal candidates are ranked lexicographically by critical path, then area, then power. Exact q8 and bf16 reciprocal normalization remain unmeasured hardware gaps and are not compared as accepted PPA.

Replace the q8 reciprocal normalization heuristic with merged RTLGen/OpenROAD datapath evidence while preserving quality gates from the decoder sweep.

## Quality And Normalization PPA

| template | role | gate | next-token | top-k | norm mode | recip bits | rank source | critical_path_ns | die_area | total_power_mw |
|---|---|---|---:|---:|---|---:|---|---:|---:|---:|
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 10 | `measured_q8_reciprocal_datapath_ppa` | 5.6126 | 39776.3136 | 0.00463 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 12 | `measured_q8_reciprocal_datapath_ppa` | 5.7554 | 52118.607025 | 0.014 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 14 | `measured_q8_reciprocal_datapath_ppa` | 5.7617 | 52360.880625 | 0.00637 |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` | `q8_reciprocal_candidate` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_quantized` | 16 | `measured_q8_reciprocal_datapath_ppa` | 5.814 | 45315.765625 | 0.0321 |
| `grid_approx_pwl_bf16_path` | `bf16_primary_anchor` | `exact_safe_survivor` | 24/24 | 24/24 | `reciprocal_float` |  | `unmeasured_gap` |  |  |  |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `q8_exact_normalization_baseline` | `exact_safe_survivor` | 24/24 | 24/24 | `exact` |  | `unmeasured_gap` |  |  |  |

## Blocked Rows

- none

## Next Step

- Measure bf16 reciprocal/multiply normalization before making a q8-versus-bf16 hardware decision.
- Measure or model q8 exact normalization only if it remains a candidate beyond the reciprocal path.
