# Llama7B Macro-Backed RMSNorm Latency Composition

- decision: `latency_sensitivity_only_pending_routed_ppa`
- baseline candidate: `score32_exp_lut_hbm_dram_service_closure_best`
- baseline latency: `12532.357427 us`
- RMSNorm rows/token: `65`
- baseline scope proof: `verified_attention_only_excludes_transformer_rmsnorm`

| RMSNorm candidate | cycles/row | cycles/token |
| --- | ---: | ---: |
| `macro_banked_conservative` | 1800 | 117000 |
| `macro_banked_three_credit` | 1035 | 67275 |

| RMSNorm candidate | clock ns | hidden fraction | raw norm us | exposed norm us | composed us | token/s | increase |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `macro_banked_conservative` | 10 | 0.0 | 1170.000 | 1170.000 | 13702.357 | 72.980 | 9.336% |
| `macro_banked_conservative` | 10 | 0.5 | 1170.000 | 585.000 | 13117.357 | 76.235 | 4.668% |
| `macro_banked_conservative` | 10 | 1.0 | 1170.000 | 0.000 | 12532.357 | 79.793 | 0.000% |
| `macro_banked_conservative` | 14 | 0.0 | 1638.000 | 1638.000 | 14170.357 | 70.570 | 13.070% |
| `macro_banked_conservative` | 14 | 0.5 | 1638.000 | 819.000 | 13351.357 | 74.899 | 6.535% |
| `macro_banked_conservative` | 14 | 1.0 | 1638.000 | 0.000 | 12532.357 | 79.793 | 0.000% |
| `macro_banked_conservative` | 18 | 0.0 | 2106.000 | 2106.000 | 14638.357 | 68.314 | 16.804% |
| `macro_banked_conservative` | 18 | 0.5 | 2106.000 | 1053.000 | 13585.357 | 73.609 | 8.402% |
| `macro_banked_conservative` | 18 | 1.0 | 2106.000 | 0.000 | 12532.357 | 79.793 | 0.000% |
| `macro_banked_three_credit` | 10 | 0.0 | 672.750 | 672.750 | 13205.107 | 75.728 | 5.368% |
| `macro_banked_three_credit` | 10 | 0.5 | 672.750 | 336.375 | 12868.732 | 77.708 | 2.684% |
| `macro_banked_three_credit` | 10 | 1.0 | 672.750 | 0.000 | 12532.357 | 79.793 | 0.000% |
| `macro_banked_three_credit` | 14 | 0.0 | 941.850 | 941.850 | 13474.207 | 74.216 | 7.515% |
| `macro_banked_three_credit` | 14 | 0.5 | 941.850 | 470.925 | 13003.282 | 76.904 | 3.758% |
| `macro_banked_three_credit` | 14 | 1.0 | 941.850 | 0.000 | 12532.357 | 79.793 | 0.000% |
| `macro_banked_three_credit` | 18 | 0.0 | 1210.950 | 1210.950 | 13743.307 | 72.763 | 9.663% |
| `macro_banked_three_credit` | 18 | 0.5 | 1210.950 | 605.475 | 13137.832 | 76.116 | 4.831% |
| `macro_banked_three_credit` | 18 | 1.0 | 1210.950 | 0.000 | 12532.357 | 79.793 | 0.000% |

## Blockers

- routed timing, area, and power for the macro-backed RMSNorm are pending
- the amount of RMSNorm overlap with attention/MLP execution is not measured
- activity-backed RMSNorm energy is unavailable

The source equation proves the attention baseline excludes transformer RMSNorm, so the zero-hidden row is a non-double-counted serialized increment and the fully hidden row is the overlap lower bound. The three-credit candidate is performance-preferred at every matched clock/overlap point, but this does not establish PPA dominance. Do not rerank PPA or claim final full-model latency until routed clock, overlap, area, and activity evidence are available.
