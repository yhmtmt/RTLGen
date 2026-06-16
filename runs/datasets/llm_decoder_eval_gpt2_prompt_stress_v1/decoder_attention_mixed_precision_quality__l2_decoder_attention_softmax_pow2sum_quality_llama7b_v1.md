# Llama7B Attention Mixed-Precision Quality Proxy

- decision: `mixed_precision_quality_blocked`
- best quality candidate: `q8_k8_v6_a24_s8_w8_softmax_rtl_exact`
- best low-cost candidate: `None`
- passing candidates: `0`
- borderline candidates: `0`
- dual-stream required density gain: `2.011289`
- recommended next step: `hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery`

## Candidate Summary

| candidate | softmax | q | k | v | acc | score | weight | top1 | retrieval | cosine | kl | decision |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| q8_k8_v6_a24_s8_w8_softmax_rtl_exact | rtl_exact | 8 | 8 | 6 | 24 | 8 | 8 | 0.998047 | 1.0 | 0.861212 | 0.741326 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_pow2sum | rtl_pow2sum | 8 | 8 | 6 | 24 | 8 | 8 | 0.998047 | 1.0 | 0.859392 | 7.446566 | mixed_precision_risky |

## Regime Summary

| candidate | softmax | regime | top1 | retrieval | cosine | kl | decision |
|---|---|---|---:|---:|---:|---:|---|
| q8_k8_v6_a24_s8_w8_softmax_rtl_exact | rtl_exact | native_correlated_queries | 1.0 | 1.0 | 0.997123 | 0.526018 | mixed_precision_borderline |
| q8_k8_v6_a24_s8_w8_softmax_rtl_exact | rtl_exact | native_low_margin | 0.992188 | 0.0 | 0.918042 | 0.874315 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_exact | rtl_exact | native_random | 1.0 | 0.0 | 0.560888 | 1.020557 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_exact | rtl_exact | native_retrieval | 1.0 | 1.0 | 0.968794 | 0.544414 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_pow2sum | rtl_pow2sum | native_correlated_queries | 1.0 | 1.0 | 0.999644 | 0.757035 | mixed_precision_borderline |
| q8_k8_v6_a24_s8_w8_softmax_rtl_pow2sum | rtl_pow2sum | native_low_margin | 0.992188 | 0.0 | 0.916575 | 7.60476 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_pow2sum | rtl_pow2sum | native_random | 1.0 | 0.0 | 0.521351 | 20.727391 | mixed_precision_risky |
| q8_k8_v6_a24_s8_w8_softmax_rtl_pow2sum | rtl_pow2sum | native_retrieval | 1.0 | 1.0 | 1.0 | 0.697078 | mixed_precision_borderline |

## Assumptions

- This is a Llama7B-shape synthetic native-GQA attention proxy, not measured Llama7B perplexity or task accuracy.
- The proxy uses 32 attention heads, 4 KV heads, and head_dim 128 by default to match the current GQA8 Llama7B frontier assumption.
- Q/K/V use per-vector symmetric quantization; accumulator saturation models fixed-width integer dot products.
- The rtl_exact and rtl_pow2sum modes model the int8 row-softmax RTL: score quantization, clipped exp powers, 127-scale output weights, and either exact or power-of-two sum normalization.
- Passing this proxy is only a gate for mixed-precision RTL/PPA and later real-checkpoint validation.
