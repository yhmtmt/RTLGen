# Llama7B Macro-Backed RMSNorm Latency Composition

- decision: `latency_sensitivity_only_pending_routed_ppa`
- baseline candidate: `score32_exp_lut_hbm_dram_service_closure_best`
- baseline latency: `12532.357427 us`
- RMSNorm rows/token: `65`
- RMSNorm cycles/row: `1800`
- RMSNorm service cycles/token: `117000`

| clock ns | hidden fraction | raw norm us | exposed norm us | composed us | token/s | increase |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 0.0 | 1170.000 | 1170.000 | 13702.357 | 72.980 | 9.336% |
| 10 | 0.5 | 1170.000 | 585.000 | 13117.357 | 76.235 | 4.668% |
| 10 | 1.0 | 1170.000 | 0.000 | 12532.357 | 79.793 | 0.000% |
| 14 | 0.0 | 1638.000 | 1638.000 | 14170.357 | 70.570 | 13.070% |
| 14 | 0.5 | 1638.000 | 819.000 | 13351.357 | 74.899 | 6.535% |
| 14 | 1.0 | 1638.000 | 0.000 | 12532.357 | 79.793 | 0.000% |
| 18 | 0.0 | 2106.000 | 2106.000 | 14638.357 | 68.314 | 16.804% |
| 18 | 0.5 | 2106.000 | 1053.000 | 13585.357 | 73.609 | 8.402% |
| 18 | 1.0 | 2106.000 | 0.000 | 12532.357 | 79.793 | 0.000% |

## Blockers

- routed timing, area, and power for the macro-backed RMSNorm are pending
- the amount of RMSNorm overlap with attention/MLP execution is not measured
- the current attention frontier does not prove whether its latency already includes any normalization allowance
- activity-backed RMSNorm energy is unavailable

Use the zero-hidden row as a serialized upper-bound increment and the fully hidden row as the unchanged-baseline lower bound. Do not rerank PPA or claim full-model latency until routed clock, overlap, area, and activity evidence are available.
