# Decoder Attention/KV Quality Proxy

- model: `llm_decoder_attention_kv_quality_proxy_v1`
- metric_row_count: `2560`
- candidates: `5`

## Candidate Summary

| candidate | top1 | retrieval | cosine | kl | decision |
|---|---:|---:|---:|---:|---|
| gqa8_kv4 | 0.320312 | 0.582031 | 0.361654 | 1.256327 | quality_experiment_risky |
| gqa8_kv8 | 0.326172 | 0.585938 | 0.363455 | 1.255761 | proxy_risk_needs_model_native_eval |
| mha_kv4 | 0.953125 | 1.0 | 0.994478 | 0.003063 | quality_experiment_risky |
| mha_kv8 | 1.0 | 1.0 | 0.999984 | 9e-06 | proxy_pass |
| mqa_kv4 | 0.273438 | 0.527344 | 0.305449 | 1.482494 | bound_only_retraining_required |

## Regime Summary

| candidate | regime | top1 | retrieval | cosine | kl | decision |
|---|---|---:|---:|---:|---:|---|
| gqa8_kv4 | correlated_heads | 1.0 | 1.0 | 0.991796 | 0.004833 | quality_experiment_risky |
| gqa8_kv4 | independent_heads | 0.015625 | 0.0 | 0.238882 | 0.426909 | quality_experiment_risky |
| gqa8_kv4 | low_margin | 0.101562 | 0.0 | 0.210438 | 0.481443 | quality_experiment_risky |
| gqa8_kv4 | retrieval | 0.164062 | 0.164062 | 0.005499 | 4.112122 | quality_experiment_risky |
| gqa8_kv8 | correlated_heads | 1.0 | 1.0 | 0.996717 | 0.001969 | proxy_pass |
| gqa8_kv8 | independent_heads | 0.015625 | 0.0 | 0.239835 | 0.426176 | proxy_risk_needs_model_native_eval |
| gqa8_kv8 | low_margin | 0.117188 | 0.0 | 0.211347 | 0.481491 | proxy_risk_needs_model_native_eval |
| gqa8_kv8 | retrieval | 0.171875 | 0.171875 | 0.005922 | 4.113409 | proxy_risk_needs_model_native_eval |
| mha_kv4 | correlated_heads | 1.0 | 1.0 | 0.994816 | 0.003355 | quality_experiment_risky |
| mha_kv4 | independent_heads | 0.875 | 0.0 | 0.990397 | 0.004775 | quality_experiment_risky |
| mha_kv4 | low_margin | 0.9375 | 0.0 | 0.993184 | 0.002647 | quality_experiment_risky |
| mha_kv4 | retrieval | 1.0 | 1.0 | 0.999514 | 0.001475 | quality_experiment_promising |
| mha_kv8 | correlated_heads | 1.0 | 1.0 | 0.999985 | 1.1e-05 | proxy_pass |
| mha_kv8 | independent_heads | 1.0 | 0.0 | 0.999972 | 1.4e-05 | proxy_pass |
| mha_kv8 | low_margin | 1.0 | 0.0 | 0.999979 | 8e-06 | proxy_pass |
| mha_kv8 | retrieval | 1.0 | 1.0 | 0.999999 | 4e-06 | proxy_pass |
| mqa_kv4 | correlated_heads | 1.0 | 1.0 | 0.991277 | 0.005148 | bound_only_retraining_required |
| mqa_kv4 | independent_heads | 0.007812 | 0.0 | 0.113326 | 0.47151 | bound_only_retraining_required |
| mqa_kv4 | low_margin | 0.03125 | 0.0 | 0.104382 | 0.545357 | bound_only_retraining_required |
| mqa_kv4 | retrieval | 0.054688 | 0.054688 | 0.01281 | 4.907963 | bound_only_retraining_required |

## Assumptions

- This is a controlled attention proxy, not measured LLaMA perplexity.
- GQA/MQA are modeled as post-hoc K/V head averaging, which is intentionally pessimistic for non-native GQA/MQA models.
- KV quantization is symmetric per-vector packed quantization; scales are not learned.
- Retrieval regimes align a query with a target K/V entry to stress long-context top-1 preservation.
- A native GQA model or QAT run is still required before promoting GQA/KV4 or MQA candidates.
