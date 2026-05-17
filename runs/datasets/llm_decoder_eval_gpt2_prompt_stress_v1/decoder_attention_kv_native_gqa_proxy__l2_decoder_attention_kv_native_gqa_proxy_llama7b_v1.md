# Decoder Attention/KV Native GQA Proxy

- model: `llm_decoder_attention_kv_native_gqa_proxy_v1`
- metric_row_count: `1536`
- candidates: `4`

## Candidate Summary

| candidate | top1 | retrieval | cosine | kl | decision |
|---|---:|---:|---:|---:|---|
| gqa8_kv4 | 0.992188 | 0.872396 | 0.995913 | 0.002672 | native_lowbit_promising |
| gqa8_kv8 | 0.994792 | 0.880208 | 0.999987 | 8e-06 | native_proxy_risk |
| mqa_kv4 | 0.994792 | 0.856771 | 0.996007 | 0.002387 | native_mqa_still_requires_model_evidence |
| mqa_kv8 | 1.0 | 0.851562 | 0.999988 | 8e-06 | native_mqa_still_requires_model_evidence |

## Regime Summary

| candidate | regime | top1 | retrieval | cosine | kl | decision |
|---|---|---:|---:|---:|---:|---|
| gqa8_kv4 | native_correlated_queries | 1.0 | 1.0 | 0.994807 | 0.003177 | native_proxy_risk |
| gqa8_kv4 | native_low_margin | 0.976562 | 0.617188 | 0.993253 | 0.00286 | native_proxy_risk |
| gqa8_kv4 | native_retrieval | 1.0 | 1.0 | 0.999679 | 0.001979 | native_lowbit_promising |
| gqa8_kv8 | native_correlated_queries | 1.0 | 1.0 | 0.999984 | 1e-05 | native_proxy_pass |
| gqa8_kv8 | native_low_margin | 0.984375 | 0.640625 | 0.999978 | 9e-06 | native_proxy_risk |
| gqa8_kv8 | native_retrieval | 1.0 | 1.0 | 0.999999 | 5e-06 | native_proxy_pass |
| mqa_kv4 | native_correlated_queries | 1.0 | 1.0 | 0.994554 | 0.003099 | native_mqa_still_requires_model_evidence |
| mqa_kv4 | native_low_margin | 0.984375 | 0.570312 | 0.99358 | 0.002826 | native_mqa_still_requires_model_evidence |
| mqa_kv4 | native_retrieval | 1.0 | 1.0 | 0.999886 | 0.001237 | native_mqa_still_requires_model_evidence |
| mqa_kv8 | native_correlated_queries | 1.0 | 1.0 | 0.999983 | 9e-06 | native_mqa_still_requires_model_evidence |
| mqa_kv8 | native_low_margin | 1.0 | 0.554688 | 0.999981 | 9e-06 | native_mqa_still_requires_model_evidence |
| mqa_kv8 | native_retrieval | 1.0 | 1.0 | 1.0 | 5e-06 | native_mqa_still_requires_model_evidence |

## Assumptions

- This is a native-sharing proxy, not measured LLaMA perplexity.
- Each candidate is compared against a same-sharing KV16 reference, so GQA is not penalized for differing from MHA.
- KV8 and KV4 use symmetric per-vector packed quantization without learned scales.
- Passing this proxy only justifies a model-native GQA or QAT evaluation; it does not promote a final hardware format.
