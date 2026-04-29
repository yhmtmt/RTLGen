# Analysis Report

Local prompt-stress smoke used 24 samples and 10 survivor or boundary grid
points. The exact candidate matched the ONNX reference on all samples.

| template | next-token match | top-k contains reference |
|---|---:|---:|
| `candidate_onnx_softmax_exact` | 24/24 | 24/24 |
| `grid_logits_q8` | 24/24 | 24/24 |
| `grid_logits_q6` | 22/24 | 24/24 |
| `grid_logits_q4` | 20/24 | 24/24 |
| `grid_prob_bf16` | 24/24 | 24/24 |
| `grid_prob_fp16` | 24/24 | 24/24 |
| `grid_prob_fp8_e5m2` | 13/24 | 17/24 |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | 24/24 | 24/24 |
| `grid_approx_pwl_in_q6_w_q6_norm_recip_q10` | 22/24 | 24/24 |
| `grid_approx_pwl_bf16_path` | 24/24 | 24/24 |

Early interpretation: q8 logits, bf16/fp16 final probability, PWL q8, and PWL
bf16 remain robust on this prompt-stress set. q6 remains top-k stable but loses
next-token exactness on two prompts. fp8_e5m2 is not robust enough for the next
hardware-cost step without additional mitigation.
