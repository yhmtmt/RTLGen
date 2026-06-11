# Llama7B Attention Mixed-Precision Quality Proxy

- decision: `mixed_precision_quality_candidate_found`
- best quality candidate: `q8_k8_v8_a24_s24_w16`
- best low-cost candidate: `q8_k8_v6_a24_s24_w16`
- passing candidates: `3`
- borderline candidates: `1`
- dual-stream required density gain: `2.011289`
- recommended next step: `run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion`

## Candidate Summary

| candidate | q | k | v | acc | score | weight | top1 | retrieval | cosine | kl | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| q8_k8_v8_a24_s16_w12 | 8 | 8 | 8 | 24 | 16 | 12 | 1.0 | 1.0 | 0.999971 | 0.009549 | mixed_precision_borderline |
| q8_k8_v6_a24_s24_w16 | 8 | 8 | 6 | 24 | 24 | 16 | 1.0 | 1.0 | 0.999722 | 1.3e-05 | mixed_precision_proxy_pass |
| q8_k8_v8_a20_s24_w16 | 8 | 8 | 8 | 20 | 24 | 16 | 1.0 | 1.0 | 0.999974 | 1.3e-05 | mixed_precision_proxy_pass |
| q8_k8_v8_a24_s24_w16 | 8 | 8 | 8 | 24 | 24 | 16 | 1.0 | 1.0 | 0.999974 | 1.3e-05 | mixed_precision_proxy_pass |
| q6_k8_v8_a24_s24_w16 | 6 | 8 | 8 | 24 | 24 | 16 | 0.984375 | 1.0 | 0.999885 | 0.00012 | mixed_precision_risky |

## Regime Summary

| candidate | regime | top1 | retrieval | cosine | kl | decision |
|---|---|---:|---:|---:|---:|---|
| q6_k8_v8_a24_s24_w16 | native_correlated_queries | 1.0 | 1.0 | 0.999978 | 2e-06 | mixed_precision_proxy_pass |
| q6_k8_v8_a24_s24_w16 | native_low_margin | 0.984375 | 0.0 | 0.999911 | 0.000126 | mixed_precision_risky |
| q6_k8_v8_a24_s24_w16 | native_random | 0.953125 | 0.0 | 0.999652 | 0.000353 | mixed_precision_risky |
| q6_k8_v8_a24_s24_w16 | native_retrieval | 1.0 | 1.0 | 1.0 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v6_a24_s24_w16 | native_correlated_queries | 1.0 | 1.0 | 0.999637 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v6_a24_s24_w16 | native_low_margin | 1.0 | 0.0 | 0.999638 | 1.2e-05 | mixed_precision_risky |
| q8_k8_v6_a24_s24_w16 | native_random | 1.0 | 0.0 | 0.999611 | 3.8e-05 | mixed_precision_risky |
| q8_k8_v6_a24_s24_w16 | native_retrieval | 1.0 | 1.0 | 1.0 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v8_a20_s24_w16 | native_correlated_queries | 1.0 | 1.0 | 0.999978 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v8_a20_s24_w16 | native_low_margin | 1.0 | 0.0 | 0.999973 | 1.2e-05 | mixed_precision_risky |
| q8_k8_v8_a20_s24_w16 | native_random | 1.0 | 0.0 | 0.999944 | 3.8e-05 | mixed_precision_risky |
| q8_k8_v8_a20_s24_w16 | native_retrieval | 1.0 | 1.0 | 1.0 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v8_a24_s16_w12 | native_correlated_queries | 1.0 | 1.0 | 0.999978 | 0.030592 | mixed_precision_borderline |
| q8_k8_v8_a24_s16_w12 | native_low_margin | 1.0 | 0.0 | 0.999973 | 0.007472 | mixed_precision_risky |
| q8_k8_v8_a24_s16_w12 | native_random | 1.0 | 0.0 | 0.999933 | 0.00013 | mixed_precision_risky |
| q8_k8_v8_a24_s16_w12 | native_retrieval | 1.0 | 1.0 | 1.0 | 2e-06 | mixed_precision_proxy_pass |
| q8_k8_v8_a24_s24_w16 | native_correlated_queries | 1.0 | 1.0 | 0.999978 | 0.0 | mixed_precision_proxy_pass |
| q8_k8_v8_a24_s24_w16 | native_low_margin | 1.0 | 0.0 | 0.999973 | 1.2e-05 | mixed_precision_risky |
| q8_k8_v8_a24_s24_w16 | native_random | 1.0 | 0.0 | 0.999944 | 3.8e-05 | mixed_precision_risky |
| q8_k8_v8_a24_s24_w16 | native_retrieval | 1.0 | 1.0 | 1.0 | 0.0 | mixed_precision_proxy_pass |

## Assumptions

- This is a Llama7B-shape synthetic native-GQA attention proxy, not measured Llama7B perplexity or task accuracy.
- The proxy uses 32 attention heads, 4 KV heads, and head_dim 128 by default to match the current GQA8 Llama7B frontier assumption.
- Q/K/V use per-vector symmetric quantization; accumulator saturation models fixed-width integer dot products.
- Passing this proxy is only a gate for mixed-precision RTL/PPA and later real-checkpoint validation.
