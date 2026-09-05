# Llama7B Macro-Backed RMSNorm Latency Composition

- decision: `latency_sensitivity_only_pending_routed_ppa`
- baseline candidate: `score32_exp_lut_schedule_wrapper_hbm_controller_replay_best`
- baseline latency: `12814.257853 us`
- RMSNorm rows/token: `65`
- baseline scope proof: `verified_attention_only_excludes_transformer_rmsnorm`

| RMSNorm candidate | cycles/row | cycles/token |
| --- | ---: | ---: |
| `macro_banked_conservative` | 1800 | 117000 |
| `macro_banked_three_credit` | 1035 | 67275 |

| RMSNorm candidate | clock ns | hidden fraction | raw norm us | exposed norm us | composed us | token/s | increase |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `macro_banked_conservative` | 10 | 0.0 | 1170.000 | 1170.000 | 13984.258 | 71.509 | 9.130% |
| `macro_banked_conservative` | 10 | 0.5 | 1170.000 | 585.000 | 13399.258 | 74.631 | 4.565% |
| `macro_banked_conservative` | 10 | 1.0 | 1170.000 | 0.000 | 12814.258 | 78.038 | 0.000% |
| `macro_banked_conservative` | 14 | 0.0 | 1638.000 | 1638.000 | 14452.258 | 69.193 | 12.783% |
| `macro_banked_conservative` | 14 | 0.5 | 1638.000 | 819.000 | 13633.258 | 73.350 | 6.391% |
| `macro_banked_conservative` | 14 | 1.0 | 1638.000 | 0.000 | 12814.258 | 78.038 | 0.000% |
| `macro_banked_conservative` | 18 | 0.0 | 2106.000 | 2106.000 | 14920.258 | 67.023 | 16.435% |
| `macro_banked_conservative` | 18 | 0.5 | 2106.000 | 1053.000 | 13867.258 | 72.112 | 8.217% |
| `macro_banked_conservative` | 18 | 1.0 | 2106.000 | 0.000 | 12814.258 | 78.038 | 0.000% |
| `macro_banked_three_credit` | 10 | 0.0 | 672.750 | 672.750 | 13487.008 | 74.145 | 5.250% |
| `macro_banked_three_credit` | 10 | 0.5 | 672.750 | 336.375 | 13150.633 | 76.042 | 2.625% |
| `macro_banked_three_credit` | 10 | 1.0 | 672.750 | 0.000 | 12814.258 | 78.038 | 0.000% |
| `macro_banked_three_credit` | 14 | 0.0 | 941.850 | 941.850 | 13756.108 | 72.695 | 7.350% |
| `macro_banked_three_credit` | 14 | 0.5 | 941.850 | 470.925 | 13285.183 | 75.272 | 3.675% |
| `macro_banked_three_credit` | 14 | 1.0 | 941.850 | 0.000 | 12814.258 | 78.038 | 0.000% |
| `macro_banked_three_credit` | 18 | 0.0 | 1210.950 | 1210.950 | 14025.208 | 71.300 | 9.450% |
| `macro_banked_three_credit` | 18 | 0.5 | 1210.950 | 605.475 | 13419.733 | 74.517 | 4.725% |
| `macro_banked_three_credit` | 18 | 1.0 | 1210.950 | 0.000 | 12814.258 | 78.038 | 0.000% |

## Blockers

- routed timing, area, and power for the macro-backed RMSNorm are pending
- the amount of RMSNorm overlap with attention/MLP execution is not measured
- activity-backed RMSNorm energy is unavailable

The source equation proves the attention baseline excludes transformer RMSNorm, so the zero-hidden row is a non-double-counted serialized increment and the fully hidden row is the overlap lower bound. The three-credit candidate is performance-preferred at every matched clock/overlap point, but this does not establish PPA dominance. Do not rerank PPA or claim final full-model latency until routed clock, overlap, area, and activity evidence are available.
